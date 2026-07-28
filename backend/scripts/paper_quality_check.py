"""论文自动化质检脚本 — 对照国赛评分标准抓硬伤。

用法:
    python scripts/paper_quality_check.py <paper.md>
    python scripts/paper_quality_check.py output_paper.md --json

检查分两类:
  A. 合规硬伤 — 机器能客观判定的结构/格式/证据问题
  B. 洞察质量 — 启发式检查（灵敏度分析实质性、摘要信息量等）

输出: 逐条 PASS/FAIL + 总分。供"跑真题→质检→打磨"迭代闭环使用。
"""
import re
import sys
import json
from pathlib import Path

# Windows 控制台默认 GBK，统一输出 UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


# ── 必需章节（国赛标准结构）────────────────────────────────────────
REQUIRED_SECTIONS = [
    ("摘要", r"摘\s*要"),
    ("问题重述", r"问题重述"),
    ("问题分析", r"问题分析"),
    ("模型假设与符号说明", r"(模型假设|假设与符号|符号说明)"),
    ("模型的建立与求解", r"(模型的建立与求解|模型建立与求解|建立与求解)"),
    ("模型检验与灵敏度分析", r"(灵敏度|模型检验|检验与灵敏度)"),
    ("模型评价与改进", r"(模型评价|评价与改进)"),
    ("参考文献", r"参考文献"),
]


def _extract_abstract(text: str) -> str:
    """提取摘要章节内容（到下一个二级标题为止）。"""
    m = re.search(r"##\s*摘\s*要(.*?)(?=\n##\s|\Z)", text, re.DOTALL)
    return m.group(1).strip() if m else ""


def _has_number(s: str) -> bool:
    """判断一段文本里是否含具体数值结果。"""
    # 数字（可含小数/百分号/科学计数），排除纯年份编号
    nums = re.findall(r"\d+(?:\.\d+)?\s*(?:%|元|吨|km|公里|件|个|天|小时)?", s)
    return len(nums) >= 2


def check_paper(text: str) -> dict:
    """对论文全文跑质检，返回 {checks: [...], score, passed, failed}。"""
    checks = []

    def add(category, name, ok, detail=""):
        checks.append({"category": category, "check": name, "pass": bool(ok), "detail": detail})

    # ── A. 合规硬伤 ──
    # A1 必需章节齐全
    missing = [name for name, pat in REQUIRED_SECTIONS if not re.search(pat, text)]
    add("合规", "必需章节齐全", not missing,
        f"缺失: {', '.join(missing)}" if missing else "8 个必需章节均在")

    # A2 摘要含具体数值
    abstract = _extract_abstract(text)
    add("合规", "摘要含具体数值结果", abstract and _has_number(abstract),
        "摘要中检测到量化结果" if abstract and _has_number(abstract) else "摘要无数字或为空（黄金400字要求含真实结果）")

    # A3 摘要无公式/图表编号
    abstract_bad = bool(re.search(r"(\$|\\frac|图\s*\d|表\s*\d|图[一二三四五])", abstract))
    add("合规", "摘要无公式/图表编号", abstract and not abstract_bad,
        "摘要混入了公式或图/表编号" if abstract_bad else "干净")

    # A4 无重复章节标题
    h2 = re.findall(r"^##\s+(.+)$", text, re.MULTILINE)
    dup = {h for h in h2 if h2.count(h) > 1}
    add("合规", "无重复章节", not dup, f"重复标题: {dup}" if dup else "无重复")

    # A5 假设不重复（检查"假设"列表条目前缀重复）
    add("合规", "假设章节唯一", len(re.findall(r"模型假设", text)) <= 2,
        "假设在多处重复展开" if len(re.findall(r"模型假设", text)) > 2 else "假设集中定义")

    # A6 图表引用有效（有 ![...](...) 且为 /api/images 或 http）
    imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)
    valid_imgs = [u for u in imgs if u.startswith(("/api/images", "http"))]
    add("合规", "图表引用有效", len(valid_imgs) >= 1,
        f"有效图表 {len(valid_imgs)} 张" if valid_imgs else "全文无有效图表引用（每小问应配证据图）")

    # A7 核心章有公式块
    has_math_block = "$$" in text or re.search(r"\\\[[\s\S]*?\\\]", text)
    add("合规", "模型公式以公式块呈现", has_math_block,
        "检测到 $$ 公式块" if has_math_block else "无 $$ 公式块（目标函数/约束应用公式块）")

    # A8 参考文献格式与数量
    refs = re.findall(r"^\s*\[\d+\]", text, re.MULTILINE)
    add("合规", "参考文献≥3条且编号", len(refs) >= 3,
        f"检测到 {len(refs)} 条编号文献" if refs else "无编号参考文献")

    # ── B. 洞察质量（启发式）──
    # B1 灵敏度分析有实质内容（不只是标题）
    sens = re.search(r"(灵敏度|敏感性)([\s\S]{200,}?)(?=\n##\s|\Z)", text)
    sens_substantive = bool(sens) and (_has_number(sens.group(0)) or "稳健" in sens.group(0) or "变化" in sens.group(0))
    add("洞察", "灵敏度分析有实质内容", sens_substantive,
        "灵敏度章节含数值/稳健性结论" if sens_substantive else "灵敏度分析缺失或流于形式（独立给分项）")

    # B2 每个子问题有结果检验（核心章出现"检验/验证/合理性"）
    core = re.search(r"模型的建立与求解([\s\S]*?)(?=\n##\s*(五|模型检验)|\Z)", text)
    core_text = core.group(0) if core else ""
    has_verify = bool(re.search(r"(检验|验证|合理性|量纲|边界)", core_text))
    add("洞察", "子问题结果有检验", has_verify and _has_number(core_text),
        "核心章含检验与数值" if has_verify and _has_number(core_text) else "核心章缺结果检验（评分三段式之一）")

    # B3 摘要结论具体（含"最优/最小/最大/提升/降低"等结论词 + 数字）
    abstract_conclusion = bool(re.search(r"(最优|最小|最大|提升|降低|减少|增长)", abstract)) and _has_number(abstract)
    add("洞察", "摘要结论具体非空话", abstract_conclusion,
        "摘要有具体结论" if abstract_conclusion else "摘要结论泛泛（应含最优值等具体结论）")

    # B4 模型与求解不落空（核心章引用了第三章定义的符号）
    add("洞察", "建模与求解衔接", bool(core_text) and "$" in core_text,
        "核心章使用公式符号" if core_text and "$" in core_text else "核心章几乎无公式（疑似模型求解两张皮）")

    passed = sum(1 for c in checks if c["pass"])
    total = len(checks)
    return {
        "checks": checks,
        "passed": passed,
        "total": total,
        "score": round(passed / total * 100, 1) if total else 0,
    }


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    paper_path = Path(sys.argv[1])
    if not paper_path.exists():
        print(f"文件不存在: {paper_path}")
        sys.exit(1)

    text = paper_path.read_text(encoding="utf-8")
    result = check_paper(text)

    if "--json" in sys.argv:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # 人类可读报告
    print("=" * 62)
    print(f"论文质检报告 — {paper_path.name}")
    print("=" * 62)
    for cat in ("合规", "洞察"):
        print(f"\n【{cat}】")
        for c in result["checks"]:
            if c["category"] != cat:
                continue
            mark = "[OK]" if c["pass"] else "[NG]"
            print(f"  {mark} {c['check']}")
            if not c["pass"] and c["detail"]:
                print(f"      └ {c['detail']}")
    print("\n" + "-" * 62)
    print(f"总分: {result['passed']}/{result['total']}  ({result['score']}%)")
    grade = "优秀" if result["score"] >= 90 else "良好" if result["score"] >= 75 else "需改进"
    print(f"评级: {grade}")
    print("-" * 62)


if __name__ == "__main__":
    main()
