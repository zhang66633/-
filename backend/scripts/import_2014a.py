"""导入 2014A 嫦娥三号论文（ZIP 中有 1 篇可直接提取）。"""
import sys, zipfile, tempfile, shutil, os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from app.services.kb_extractor import KBExtractor

ZIP_PATH = Path(r"D:\_Documents\2026全国大学生数学建模国赛资料大全\A历年国赛获奖论文（1992-2025）\2014国赛获奖论文\2014年国赛一等奖A嫦娥三号软着陆轨道设计与控制策略-华南农业大学-论文.zip")

tmp = tempfile.mkdtemp()
try:
    with zipfile.ZipFile(ZIP_PATH) as zf:
        pdfs = [n for n in zf.namelist() if n.lower().endswith('.pdf')]
        if not pdfs:
            print("No PDF found in archive")
            sys.exit(1)
        zf.extractall(tmp)

    pdf_path = None
    for root, dirs, files in os.walk(tmp):
        for f in files:
            if f.lower().endswith('.pdf'):
                pdf_path = Path(root) / f
                break

    if not pdf_path:
        print("PDF not found after extraction")
        sys.exit(1)

    print(f"PDF: {pdf_path.name} ({pdf_path.stat().st_size/1024:.0f} KB)")

    extractor = KBExtractor()
    pdf_data = pdf_path.read_bytes()
    text = extractor.extract_pdf_text(pdf_data)
    print(f"Text: {len(text)} chars")

    result = extractor.extract_paper(text, pdf_path.name)
    if result["status"] == "error":
        print(f"Extraction failed: {result['error']}")
        sys.exit(1)

    paper = result["data"]
    title = paper.get("paper", {}).get("title", "?")
    print(f"Title: {title}")

    yaml_path = extractor.write_paper(paper)
    print(f"Written: {yaml_path}")

    try:
        extractor.embed_new(yaml_path)
        print("Embedded OK")
    except Exception as e:
        print(f"Embed failed (will fix on reindex): {e}")

finally:
    shutil.rmtree(tmp)
