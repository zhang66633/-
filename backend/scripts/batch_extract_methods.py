"""从算法全收录 PDF 按章节提取方法卡片。

用法:
    python scripts/batch_extract_methods.py --dry-run   # 仅预览章节
    python scripts/batch_extract_methods.py              # 正式提取
    python scripts/batch_extract_methods.py --skip-embed # 不向量化
"""

import re
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.kb_extractor import KBExtractor
from app.knowledge.loader import KnowledgeBaseLoader
from app.config import get_settings

PDF_PATH = Path(r"D:\_Documents\2026全国大学生数学建模国赛资料大全\国赛数模相关书籍\数学建模算法全收录800页.pdf")

# 章节名 → 建议的 category 映射
CHAPTER_CATEGORY_MAP = {
    "线性规划": ["优化"],
    "整数规划": ["优化"],
    "非线性规划": ["优化"],
    "动态规划": ["优化"],
    "图与网络": ["图论"],
    "排队论": ["排队论", "随机过程"],
    "对策论": ["博弈论"],
    "层次分析法": ["评价"],
    "插值与拟合": ["数值方法", "统计分析"],
    "数据的统计描述和分析": ["统计分析"],
    "方差分析": ["统计分析"],
    "回归分析": ["统计分析", "预测"],
    "微分方程建模": ["微分方程"],
    "稳定状态模型": ["微分方程"],
    "常微分方程的解法": ["微分方程", "数值方法"],
    "差分方程模型": ["微分方程"],
    "马氏链模型": ["随机过程", "预测"],
    "变分法模型": ["微分方程", "优化"],
    "神经网络模型": ["机器学习", "预测"],
    "偏微分方程的数值解": ["微分方程", "数值方法"],
    "目标规划": ["优化"],
    "模糊数学模型": ["评价", "分类"],
    "现代优化算法": ["优化", "启发式算法"],
    "时间序列模型": ["预测"],
    "存贮论": ["优化", "运筹学"],
    "经济与金融中的优化问题": ["优化", "经济学"],
    "生产与服务运作管理中的优化问题": ["优化", "运筹学"],
    "灰色系统理论及其应用": ["预测"],
    "多元分析": ["统计分析", "分类"],
    "偏最小二乘回归": ["统计分析", "预测"],
}


def existing_card_names() -> set[str]:
    """获取已有方法卡片名称集合（用于去重）。"""
    settings = get_settings()
    loader = KnowledgeBaseLoader(settings.kb_root)
    names = {c.name for c in loader.load_all_methods()}
    # 部分已有卡片的别名映射
    aliases = {
        "线性规划", "整数规划", "非线性规划", "动态规划",
        "图论", "最短路径", "层次分析法", "模糊综合评价",
        "回归分析", "多元线性回归", "Logistic回归",
        "聚类分析", "主成分分析", "支持向量机",
        "ARIMA", "灰色预测", "BP神经网络", "LSTM",
        "蒙特卡洛", "模拟退火", "遗传算法", "粒子群算法",
        "TOPSIS", "DEA", "熵权法", "假设检验", "方差分析",
        "网络流与最小生成树", "NSGA-II",
    }
    return names | aliases


def split_chapters(text: str) -> list[tuple[str, str]]:
    """按'第X章'分割文本，返回[(章名, 内容), ...]"""
    # 匹配: 第一章 线性规划 / 第二章  整数规划 等
    pattern = r'第([一二三四五六七八九十百零\d]+)章\s+(.+?)(?=\n第[一二三四五六七八九十百零\d]+章|\Z)'
    # 简单做法：用 regex 找到所有章节起始位置
    chapter_starts = list(re.finditer(
        r'第[一二三四五六七八九十百零\d]+章\s+\S+',
        text
    ))

    chapters = []
    for i, match in enumerate(chapter_starts):
        chap_title = match.group().strip()
        start = match.start()
        end = chapter_starts[i + 1].start() if i + 1 < len(chapter_starts) else len(text)
        content = text[start:end].strip()
        # 跳过附录和目录
        if any(skip in chap_title for skip in ("附录", "参考", "目录")):
            continue
        # 跳过目录页假章节：标题带 ……… 页码引导线或以纯数字结尾（如 "线性规划………1"）
        if re.search(r"[…·]{3,}", chap_title) or re.search(r"\s\d{1,4}$", chap_title):
            continue
        chapters.append((chap_title, content))

    return chapters


def main(dry_run: bool = False, skip_embed: bool = False, pdf_path: Path | None = None):
    pdf_path = pdf_path or PDF_PATH
    existing = existing_card_names()
    extractor = KBExtractor()

    print(f"已有方法卡片: {len(existing)} 张")
    print(f"读取 PDF: {pdf_path}")

    if not pdf_path.exists():
        print(f"[FAIL] PDF 不存在: {pdf_path}")
        return

    pdf_data = pdf_path.read_bytes()
    print(f"PDF 大小: {len(pdf_data)/1024:.0f} KB")

    text = extractor.extract_pdf_text(pdf_data, max_chars=999999)
    print(f"提取文本: {len(text):,} 字符")

    chapters = split_chapters(text)
    print(f"识别章节: {len(chapters)} 章\n")

    success = 0
    skip_count = 0
    fail = 0

    for chap_title, content in chapters:
        # 解析章名
        chap_name = re.sub(r'第[一二三四五六七八九十百零\d]+章\s*', '', chap_title).strip()
        cat = CHAPTER_CATEGORY_MAP.get(chap_name, ["其他"])

        # 去重：跳过已有卡片
        should_skip = False
        for kw in [chap_name] + chap_name.split("与") + chap_name.split("和"):
            for name in existing:
                if kw.strip() in name or name in kw.strip():
                    should_skip = True
                    break

        print(f"{'='*50}")
        print(f"[CHAPTER] {chap_title}")
        print(f"   类别: {', '.join(cat)}")

        if should_skip:
            print(f"   [SKIP] 已有相关卡片，跳过")
            skip_count += 1
            continue

        content_len = len(content)
        print(f"   文本: {content_len:,} 字符")

        if content_len < 200:
            print(f"   [WARN] 内容太短，跳过")
            skip_count += 1
            continue

        if dry_run:
            print(f"   [dry-run] 将提取为方法卡片")
            success += 1
            continue

        # LLM 提取
        print(f"   [LLM] LLM 提取中...")
        result = extractor.extract_method(content[:8000], f"{chap_name}.txt")

        if result["status"] == "error":
            print(f"   [FAIL] 提取失败: {result['error']}")
            fail += 1
            continue

        card_data = result["data"]
        card_name = card_data.get("method_card", {}).get("name", "?")
        print(f"   [OK] 提取成功: {card_name}")

        # 写入 YAML
        try:
            yaml_path = extractor.write_method(card_data, cat[0])
            print(f"   [FILE] YAML: {yaml_path}")

            if not skip_embed:
                try:
                    extractor.embed_new(yaml_path)
                    print(f"   [EMBED] 已向量化")
                except Exception as e:
                    print(f"   [WARN] 向量化失败: {e}")
            success += 1
        except Exception as e:
            print(f"   [FAIL] 写入失败: {e}")
            fail += 1

    print(f"\n{'='*50}")
    print(f"完成: 成功 {success} | 跳过 {skip_count} | 失败 {fail}")
    print(f"总计已有: {len(existing)} → 新增 {success} → {len(existing) + success} 张")
    if not dry_run and not skip_embed:
        print("提示: 前端 /knowledge 页可搜索验证新卡片。")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-embed", action="store_true")
    parser.add_argument("--pdf", default=None, help="指定书籍 PDF 路径（默认：算法全收录800页）")
    args = parser.parse_args()
    main(
        dry_run=args.dry_run,
        skip_embed=args.skip_embed,
        pdf_path=Path(args.pdf) if args.pdf else None,
    )
