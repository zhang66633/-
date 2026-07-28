"""跑 2023 C 题端到端测试 + 自动质检。

用法:
    python scripts/run_c_problem_test.py          # 跑完整 pipeline 并质检
    python scripts/run_c_problem_test.py --check-only  # 只对已有 output_paper.md 质检

输出:
    scripts/testset/output_2023C.md   生成的论文
    终端打印质检报告（合规+洞察评分）
"""
import os
import sys

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_BACKEND_DIR)
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from dotenv import load_dotenv
load_dotenv(override=True)

from pathlib import Path

TESTSET_DIR = Path(__file__).parent / "testset"
PROBLEM_FILE = TESTSET_DIR / "2023_C_vegetable_pricing.md"
OUTPUT_FILE = TESTSET_DIR / "output_2023C.md"


def _load_problem() -> str:
    """提取题目部分（去掉参照基准），作为 pipeline 输入。"""
    raw = PROBLEM_FILE.read_text(encoding="utf-8")
    # 截取到"参照基准"之前
    cut = raw.find("## 参照基准")
    return (raw[:cut] if cut != -1 else raw).strip()


def run_pipeline():
    from app.core.state import create_initial_state
    from app.core.workflow import get_orchestrator

    problem = _load_problem()
    print("=" * 62)
    print("2023 C 题端到端测试")
    print("=" * 62)
    print(f"题目长度: {len(problem)} 字")
    print("流程: 分析 -> 建模 -> 求解(tool loop) -> 验证 -> 写作(分章节+红队)")
    print("-" * 62)

    orchestrator = get_orchestrator()
    state = create_initial_state(
        problem_raw=problem,
        mode="execute",
        session_id="test_2023C",
    )
    result = orchestrator.invoke(state, {"recursion_limit": 100})

    print(f"[分析] {len(result.get('analysis_output',''))} 字")
    print(f"[建模] {len(result.get('model_output',''))} 字")
    print(f"[求解] {len(result.get('solving_output',''))} 字")
    print(f"[验证] {len(result.get('verification_output',''))} 字")
    print(f"[写作] {len(result.get('writing_output',''))} 字")
    print(f"[最终] {len(result.get('final_response',''))} 字")

    paper = result.get("final_response") or result.get("writing_output", "")
    if paper:
        OUTPUT_FILE.write_text(paper, encoding="utf-8")
        print(f"\n论文已保存: {OUTPUT_FILE}")
    return paper


def run_check():
    from scripts.paper_quality_check import check_paper

    if not OUTPUT_FILE.exists():
        print(f"未找到 {OUTPUT_FILE}，请先运行完整测试。")
        return
    text = OUTPUT_FILE.read_text(encoding="utf-8")
    result = check_paper(text)

    print("\n" + "=" * 62)
    print(f"质检报告 — {OUTPUT_FILE.name}")
    print("=" * 62)
    for cat in ("合规", "洞察"):
        print(f"\n【{cat}】")
        for c in result["checks"]:
            if c["category"] != cat:
                continue
            mark = "PASS" if c["pass"] else "FAIL"
            print(f"  [{mark}] {c['check']}")
            if not c["pass"] and c["detail"]:
                print(f"        -> {c['detail']}")
    print("\n" + "-" * 62)
    print(f"总分: {result['passed']}/{result['total']}  ({result['score']}%)")
    print("-" * 62)


if __name__ == "__main__":
    if "--check-only" in sys.argv:
        run_check()
    else:
        run_pipeline()
        run_check()
