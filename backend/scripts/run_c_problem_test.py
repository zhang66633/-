"""跑 2023 C 题端到端测试 + 自动质检。

用法:
    python scripts/run_c_problem_test.py          # 跑完整 pipeline 并质检
    python scripts/run_c_problem_test.py --check-only  # 只对已有 output_paper.md 质检

输出:
    scripts/testset/output_2023C.md   生成的论文
    终端打印质检报告（合规+洞察评分）

数据文件:
    自动从 backend/data/problems/2023C/ 加载题目附件（xlsx/csv/tsv），
    如果目录不存在则降级为仅文本模式。
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
import json as _json

TESTSET_DIR = Path(__file__).parent / "testset"
PROBLEM_FILE = TESTSET_DIR / "2023_C_vegetable_pricing.md"
OUTPUT_FILE = TESTSET_DIR / "output_2023C.md"
DATA_FILES_DIR = Path(__file__).parent.parent / "data" / "problems" / "2023C"


def _load_problem() -> str:
    """提取题目部分（去掉参照基准），作为 pipeline 输入。"""
    raw = PROBLEM_FILE.read_text(encoding="utf-8")
    cut = raw.find("## 参照基准")
    return (raw[:cut] if cut != -1 else raw).strip()


def _discover_data_files() -> tuple[list[dict], str]:
    """扫描 data/problems/2023C/ 目录，提取数据文件信息。

    Returns:
        (data_files_info, data_files_dir)
    """
    if not DATA_FILES_DIR.exists():
        return [], ""

    import pandas as pd
    import io as _io

    data_files_info = []
    for f in sorted(DATA_FILES_DIR.iterdir()):
        if f.suffix.lower() not in (".xlsx", ".xls", ".csv", ".tsv", ".txt"):
            continue
        try:
            data = f.read_bytes()
            if f.suffix.lower() in (".csv", ".tsv"):
                sep = "\t" if f.suffix.lower() == ".tsv" else ","
                df = pd.read_csv(_io.StringIO(data.decode("utf-8", errors="replace")), sep=sep, nrows=5)
                total_rows = len(pd.read_csv(_io.StringIO(data.decode("utf-8", errors="replace")), sep=sep))
            else:
                df = pd.read_excel(_io.BytesIO(data), nrows=5)
                xls = pd.ExcelFile(_io.BytesIO(data))
                total_rows = len(pd.read_excel(xls, sheet_name=0))
            data_files_info.append({
                "filename": f.name,
                "columns": [str(c) for c in df.columns],
                "rows": total_rows,
            })
        except Exception as e:
            print(f"  [WARN] 数据文件读取失败 {f.name}: {e}")

    return data_files_info, str(DATA_FILES_DIR.resolve())


def run_pipeline():
    from app.core.state import create_initial_state
    from app.core.workflow import get_orchestrator

    problem = _load_problem()

    # 发现数据文件
    data_files_info, data_files_dir = _discover_data_files()
    if data_files_info:
        print(f"数据文件: {len(data_files_info)} 个")
        for df in data_files_info:
            print(f"  - {df['filename']}: {df['rows']}行, {len(df['columns'])}列")
        # 将数据文件信息追加到 problem 文本中
        data_context = "\n\n## 附件数据文件\n"
        for df in data_files_info:
            data_context += (
                f"- `{df['filename']}`: {df['rows']}行, "
                f"列: {', '.join(df['columns'])}\n"
            )
        problem = problem + data_context
    else:
        print("数据文件: 无（纯文本模式）")

    print("=" * 62)
    print("2023 C 题端到端测试")
    print("=" * 62)
    print(f"题目长度: {len(problem)} 字")
    print(f"数据文件目录: {data_files_dir or '(无)'}")
    print("流程: 分析 -> 建模 -> 求解(tool loop) -> 验证 -> 写作(分章节+红队)")
    print("-" * 62)

    orchestrator = get_orchestrator()
    state = create_initial_state(
        problem_raw=problem,
        mode="execute",
        session_id="test_2023C",
        data_files=data_files_info,
        data_files_dir=data_files_dir,
    )
    result = orchestrator.invoke(state, {"recursion_limit": 200})

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
