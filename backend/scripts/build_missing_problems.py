"""为已有论文但缺题目卡的经典赛题补建 Problem 卡。

数据源: 本地资料大全「1.历年国赛赛题」的题目 PDF/DOC（机械提取，不烧 LLM）。
标题采用人工核对过的权威名称。幂等：已有 (year, problem_id) 的自动跳过。
"""

import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from app.config import get_settings  # noqa: E402
from app.services.kb_extractor import KBExtractor  # noqa: E402

DATASET = Path(r"D:\_Documents\2026全国大学生数学建模国赛资料大全\1.历年国赛赛题（1992-2025）")

# (年份, 题号, 权威标题)
WANTED = [
    (1998, "A", "投资的收益与风险"),
    (2002, "A", "车灯线光源的优化设计"),
    (2005, "A", "长江水质的评价和预测"),
    (2008, "B", "高等教育学费标准的评价及建议"),
    (2010, "B", "上海世博会影响力的定量评估"),
    (2014, "A", "嫦娥三号软着陆轨道设计与控制"),
    (2016, "B", "小区开放对道路通行的影响"),
    (2018, "B", "智能RGV的动态调度策略"),
    (2019, "C", "机场出租车的最优决策"),
    (2020, "C", "中小微企业的信贷决策"),
    (2023, "A", "定日镜场的优化设计"),
]


def existing_keys() -> set:
    settings = get_settings()
    root = settings.kb_root / "problems"
    keys = set()
    max_id = 0
    for p in root.rglob("*.yaml"):
        if "_quarantine" in p.parts:
            continue
        try:
            d = yaml.safe_load(p.read_text(encoding="utf-8")).get("problem", {})
        except Exception:
            continue
        keys.add((d.get("year"), str(d.get("problem_id", "")).upper()))
        m = re.search(r"prob_(\d+)", p.stem)
        if m:
            max_id = max(max_id, int(m.group(1)))
    return keys, max_id


def find_problem_file(year: int, letter: str) -> Path | None:
    candidates = [d for d in DATASET.iterdir() if d.is_dir() and str(year) in d.name]
    for d in candidates:
        hits = [
            f
            for f in sorted(d.rglob("*"))
            if f.suffix.lower() in {".pdf", ".doc", ".docx"}
            and re.search(rf"(?i)[^a-z]{letter}(?:\D|$)", f.stem.replace(year.__str__(), ""))
            and len(f.stem) < 60
        ]
        # 宽松回退：任何含题号的文件名
        if not hits:
            hits = [f for f in sorted(d.rglob(f"*{letter}*")) if f.suffix.lower() in {".pdf", ".doc", ".docx"}]
        if hits:
            return hits[0]
    return None


def main():
    keys, next_num = existing_keys()
    extractor = KBExtractor()
    created, missed = [], []
    for year, letter, title in WANTED:
        if (year, letter.upper()) in keys:
            print(f"[skip] {year}{letter} 已有题目卡")
            continue
        src = find_problem_file(year, letter)
        if not src:
            missed.append((year, letter))
            print(f"[miss] {year}{letter}: 本地未找到题目文件")
            continue
        if src.suffix.lower() == ".pdf":
            text = extractor.extract_pdf_text(src.read_bytes())
        else:
            from import_problems import extract_doc_text

            text = extract_doc_text(src)
        text = (text or "").strip()[:4500]
        if sum(1 for c in text if "一" <= c <= "鿿") < 150:
            # 扫描版无文字层：降级为仅元数据卡（标题即检索信号），OCR 数字化留待后续
            text = ""
            print(f"[meta] {year}{letter}: 扫描版PDF，建仅元数据卡")
        next_num += 1
        card = {
            "problem": {
                "id": f"prob_{next_num}",
                "year": year,
                "competition": "国赛",
                "problem_id": letter,
                "title": title,
                "full_text": text,
                "background": "",
                "objectives": [],
                "data_description": "",
                "data_files": [],
                "deliverables": [],
                "tags": {"source": "local_dataset"},
            }
        }
        out = get_settings().kb_root / "problems" / f"prob_{next_num}.yaml"
        out.write_text(yaml.dump(card, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")
        created.append((year, letter, title))
        print(f"[ok]   {year}{letter} -> {out.name} ({len(text)} chars)")

    print(f"\n新建 {len(created)} 张, 未找到 {len(missed)} 个")


if __name__ == "__main__":
    main()
