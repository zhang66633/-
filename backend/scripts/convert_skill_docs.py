"""把 math-modeling-skill 的 7 份算法说明文档转换成方法卡 YAML。

来源: https://github.com/XiaoMaColtAI/math-modeling-skill (MIT, assets/*.md)
原文档已存档在 knowledge_base/methods/_source_skill_docs/。

用法:
    python scripts/convert_skill_docs.py --dry-run   # 仅预览将生成的卡片
    python scripts/convert_skill_docs.py             # 写入 YAML
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings
from app.knowledge.loader import KnowledgeBaseLoader

SRC_DIR = Path(__file__).parent.parent / "knowledge_base" / "methods" / "_source_skill_docs"

# 文件号 → (分类, 分类目录名) —— 目录沿用库内既有中文分类
FILE_CATEGORY = {
    "01": (["优化"], "优化"),
    "02": (["预测"], "预测"),
    "03": (["评价"], "评价"),
    "04": (["图论"], "图论"),
    "05": (["统计分析", "数值方法"], "统计分析"),
    "06": (["综合评价"], "评价"),
    "07": (["机器学习"], "机器学习"),
}

SECTION_HEAD = re.compile(r"^##\s+(\d+)\.\s+(.+?)\s*$", re.MULTILINE)
SUB = ["算法介绍", "适用范围", "可视化图表类型", "关键文献", "代码实现要点"]


def _split_bullets(text: str) -> list[str]:
    out = []
    for line in text.splitlines():
        m = re.match(r"^[-*•]\s*(.+)$", line.strip())
        if m and len(m.group(1)) > 2:
            out.append(m.group(1).strip())
    return out


def _extract(block: str, keyword: str) -> str:
    """取「### 关键词」小节的正文（到下一个 ### 为止）。"""
    m = re.search(rf"^###\s*{keyword}.*?$(.*?)(?=^###\s|\Z)", block, re.MULTILINE | re.DOTALL)
    return m.group(1).strip() if m else ""


def parse_file(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    num = path.stem  # "01"
    category, _dir = FILE_CATEGORY[num]
    methods = []
    heads = list(SECTION_HEAD.finditer(text))
    for i, h in enumerate(heads):
        title = h.group(2).strip()
        block = text[h.end() : heads[i + 1].start() if i + 1 < len(heads) else len(text)]
        # 中文名：去掉英文括号部分
        cn = re.sub(r"\s*[（(].*?[)）]\s*$", "", title).strip()
        en_m = re.search(r"[（(](.+?)[)）]", title)
        name_en = en_m.group(1).strip() if en_m else ""
        principle = _extract(block, SUB[0])
        if len(principle) < 40:
            continue  # 概述类伪节或内容过薄，跳过
        applicable = _split_bullets(_extract(block, SUB[1]))
        charts = _split_bullets(_extract(block, SUB[2]))
        refs = _split_bullets(_extract(block, SUB[3]))
        code_sec = _extract(block, SUB[4])
        code_blocks = re.findall(r"```python\n(.*?)```", code_sec, re.DOTALL)
        snippet = max(code_blocks, key=len)[:2500] if code_blocks else ""
        methods.append(
            {
                "name": cn,
                "name_en": name_en,
                "category": list(category),
                "principle": principle,
                "applicable_when": applicable[:8],
                "typical_scenarios": [],
                "code_snippets": (
                    [{"language": "python", "description": f"{cn} 实现要点", "code": snippet}]
                    if snippet
                    else []
                ),
                "related_papers": refs[:5],
                "difficulty": 3,
                "quality_rating": 3,
                "tags": {"key_concepts": [cn], "chart_types": charts[:6], "source": "math-modeling-skill"},
            }
        )
    return methods


def existing_names() -> set[str]:
    settings = get_settings()
    loader = KnowledgeBaseLoader(settings.kb_root)
    aliases = {
        "线性规划", "整数规划", "非线性规划", "动态规划", "图论", "最短路径",
        "层次分析法", "模糊综合评价", "回归分析", "多元线性回归", "Logistic回归",
        "聚类分析", "主成分分析", "支持向量机", "ARIMA", "灰色预测", "BP神经网络",
        "LSTM", "蒙特卡洛", "模拟退火", "遗传算法", "粒子群算法", "TOPSIS", "DEA",
        "熵权法", "假设检验", "方差分析", "网络流与最小生成树", "NSGA-II",
        "时间序列", "决策树", "随机森林", "XGBoost", "灰色关联分析", "移动平均",
        "插值", "拟合", "排队论", "博弈论", "存贮论", "目标规划", "模拟退火算法",
    }
    return {c.name for c in loader.load_all_methods()} | aliases


def main(dry_run: bool = False):
    have = existing_names()
    settings = get_settings()
    methods_dir = settings.kb_root / "methods"

    # 现有最大 mc_ 编号
    all_ids = [0]
    for p in methods_dir.rglob("*.yaml"):
        m = re.search(r"mc_(\d+)", p.stem)
        if m:
            all_ids.append(int(m.group(1)))
    next_id = max(all_ids) + 1

    created, skipped = [], []
    for src in sorted(SRC_DIR.glob("*.md")):
        for card in parse_file(src):
            nm = card["name"]
            if any(nm in e or e in nm for e in have if len(e) >= 2):
                skipped.append(nm)
                continue
            have.add(nm)
            _, dir_name = FILE_CATEGORY[src.stem]
            card["id"] = f"mc_{next_id}"
            next_id += 1
            created.append((card, dir_name))

    print(f"解析出新增卡片 {len(created)} 张，去重跳过 {len(skipped)} 个重名")
    print("跳过:", "、".join(sorted(set(skipped))[:20]))
    for c, d in created:
        print(f"  [NEW] {c['id']} {c['name']} -> {d}/")

    if dry_run or not created:
        return
    for c, d in created:
        target = methods_dir / d
        target.mkdir(parents=True, exist_ok=True)
        safe = re.sub(r"[^\w\-]+", "_", c["name"])[:40]
        out = target / f"{c['id']}_{safe}.yaml"
        wrapper = {"method_card": c}
        out.write_text(
            yaml.dump(wrapper, allow_unicode=True, sort_keys=False, width=100),
            encoding="utf-8",
        )
        print(f"写入 {out.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
