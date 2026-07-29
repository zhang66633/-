"""批量导入国赛获奖论文到知识库。

从资料大全目录读取 PDF → 提取文本 → LLM 结构化 → 写入 YAML → embed。

用法:
    python scripts/batch_import_papers.py
    python scripts/batch_import_papers.py --dry-run    # 仅预览，不写入
    python scripts/batch_import_papers.py --skip-embed # 跳过量化和embed
"""

import sys
from pathlib import Path

# .env 必须在导入 app 模块之前加载
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

# Ensure backend package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.kb_extractor import KBExtractor

# 资料大全路径
DATASET_ROOT = Path(r"D:\_Documents\2026全国大学生数学建模国赛资料大全")
PAPERS_BASE = DATASET_ROOT / "A历年国赛获奖论文（1992-2025）"

# ── 精选 10 篇标杆论文 ──
# (年份, 子目录, 文件名关键词, 题型说明)
PAPERS: list[tuple[str, str, str, str]] = [
    # === 优化类 ===
    ("1998", "1998国赛获奖论文", "投资收益与风险的优化模型.pdf", "线性规划/投资组合"),
    ("2002", "2002国赛获奖论文", "车灯线光源的优化设计(1).pdf", "数值优化/光学"),
    ("2018", "2018国赛获奖论文", "基于 0-1 规划的单 RGV 动态调度模型.pdf", "整数规划/调度"),

    # === 预测类 ===
    ("2005", "2005国赛获奖论文", "长江水质的评价和预测.pdf", "综合评价+灰色预测"),
    ("2010", "2010国赛获奖论文", "储油罐的变位识别与罐容表标定.pdf", "最小二乘拟合/数值"),

    # === 评价类 ===
    ("2008", "2008国赛获奖论文", "《关于高等教育学费标准的评价及建议》.PDF", "多因素评价/BP"),
    ("2010", "2010国赛获奖论文", "上海世博会影响力的定量评估.pdf", "综合评价/影响力"),

    # === 数据/统计类 ===
    ("2019", "2019国赛获奖论文", "基于系统模拟的机场出租车决策与安排模型.pdf", "决策仿真/排队论"),
    ("2016", "2016国赛获奖论文", "2016国赛国一B题优秀论文-小区开放道路通行影响.pdf", "交通仿真/综合评价"),

    # === 现代数据驱动 ===
    ("2020", "2020国赛获奖论文", "C109.pdf", "信贷决策/数据挖掘"),
]


def main(dry_run: bool = False, skip_embed: bool = False):
    extractor = KBExtractor()
    success_count = 0
    fail_count = 0

    for year, subdir, fname, desc in PAPERS:
        paper_dir = PAPERS_BASE / subdir
        pdf_path = paper_dir / fname

        print(f"\n{'='*60}")
        print(f"[{year}] {desc}")
        print(f"  文件: {pdf_path}")

        if not pdf_path.exists():
            # 尝试模糊匹配
            candidates = list(paper_dir.glob(f"*{fname[:8]}*")) if len(fname) > 8 else []
            if not candidates:
                candidates = list(paper_dir.glob(f"*{fname.split('.')[0][:6]}*"))
            if candidates:
                pdf_path = candidates[0]
                print(f"  → 模糊匹配到: {pdf_path.name}")
            else:
                print(f"  ❌ 文件不存在，跳过")
                fail_count += 1
                continue

        if dry_run:
            print(f"  [dry-run] 将提取: {pdf_path.name}")
            success_count += 1
            continue

        # 1. 读取 PDF + 提取文本
        print(f"  读取 PDF...")
        try:
            pdf_data = pdf_path.read_bytes()
        except Exception as e:
            print(f"  ❌ 读取失败: {e}")
            fail_count += 1
            continue

        print(f"  提取文本 ({len(pdf_data)/1024:.0f} KB)...")
        text = extractor.extract_pdf_text(pdf_data)

        if not text.strip():
            print(f"  ❌ 文本提取为空")
            fail_count += 1
            continue

        print(f"  文本长度: {len(text)} 字符")

        # 2. LLM 结构化提取
        print(f"  LLM 提取结构化信息...")
        result = extractor.extract_paper(text, pdf_path.name)

        if result["status"] == "error":
            print(f"  ❌ 提取失败: {result['error']}")
            fail_count += 1
            continue

        paper_data = result["data"]
        paper_id = result.get("paper_id", "unknown")
        title = paper_data.get("paper", {}).get("title", "?")
        print(f"  提取成功: {paper_id}")
        print(f"  标题: {title}")

        # 3. 写入 YAML
        try:
            yaml_path = extractor.write_paper(paper_data)
            print(f"  YAML 已写入: {yaml_path}")
        except Exception as e:
            print(f"  ❌ YAML 写入失败: {e}")
            fail_count += 1
            continue

        # 4. Embed
        if not skip_embed:
            try:
                count = extractor.embed_new(yaml_path)
                print(f"  向量化: {count} 篇文档")
            except Exception as e:
                print(f"  ⚠️ 向量化失败（可稍后手动 reindex）: {e}")

        success_count += 1

    # ── 汇总 ──
    print(f"\n{'='*60}")
    print(f"完成: 成功 {success_count}, 失败 {fail_count}")
    if not dry_run and not skip_embed:
        print("提示: 新论文已入库。前端 /knowledge 页可搜索验证。")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-embed", action="store_true")
    args = parser.parse_args()
    main(dry_run=args.dry_run, skip_embed=args.skip_embed)
