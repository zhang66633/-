"""从国赛资料大全导入赛题原文到 knowledge_base/problems/。

处理 PDF + .doc（old Word）+ .docx 格式混合。
同时提取附件（xlsx/csv/tsv）的表结构信息，复制原始数据文件到 data/problems/。
"""

import json as _json
import re
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.knowledge.loader import KnowledgeBaseLoader
from app.config import get_settings

DATASET = Path(r"D:\_Documents\2026全国大学生数学建模国赛资料大全\1.历年国赛赛题（1992-2025）")
DATA_DIR = Path(__file__).parent.parent / "data" / "problems"

# 已知的国赛各题题型分类（用于 tags）
PROBLEM_TYPE_MAP = {
    "A": ["优化", "物理建模", "工程"],
    "B": ["优化", "调度", "规划"],
    "C": ["数据分析", "统计", "评价"],
    "D": ["应用", "评价"],
    "E": ["分类", "管理"],
}


def extract_doc_text(path: Path) -> str:
    """从 old .doc 提取文本（UTF-16LE 解码 + 过滤）。"""
    try:
        data = path.read_bytes()
        text = data.decode("utf-16-le", errors="ignore")
        clean = re.sub(r"[^\u4e00-\u9fff\u3000-\u303f\uff00-\uffef\u0020-\u007e\n\r]", "", text)
        clean = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", clean)
        lines = []
        for line in clean.split("\n"):
            line = line.strip()
            if line and len(line) > 3:
                garbage_ratio = sum(1 for c in line if c < " " or c > "~") / max(len(line), 1)
                if garbage_ratio < 0.3:
                    lines.append(line)
        return "\n".join(lines)
    except Exception:
        return ""


def extract_docx_text(path: Path) -> str:
    """从 .docx 提取文本。"""
    try:
        from docx import Document
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception:
        return ""


def extract_problem_text(path: Path) -> str:
    """根据扩展名选择合适的提取方法。"""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        from app.services.kb_extractor import KBExtractor
        return KBExtractor.extract_pdf_text(path.read_bytes(), max_chars=99999)
    elif suffix in (".docx", ".doc"):
        text = extract_docx_text(path)
        return text or extract_doc_text(path)
    elif suffix == ".txt":
        for enc in ("utf-8", "gbk", "gb2312"):
            try:
                return path.read_text(encoding=enc)
            except Exception:
                continue
    return ""


def _extract_attachment_info(path: Path) -> dict | None:
    """从附件文件中提取列信息和前5行样例，不复制全部数据进YAML。"""
    suffix = path.suffix.lower()
    if suffix not in (".xlsx", ".xls", ".csv", ".tsv"):
        return None
    try:
        import pandas as pd
        import io as _io
        data = path.read_bytes()
        if suffix in (".csv", ".tsv"):
            sep = "\t" if suffix == ".tsv" else ","
            df = pd.read_csv(_io.StringIO(data.decode("utf-8", errors="replace")), sep=sep, nrows=5)
            # 统计总行数
            try:
                full_df = pd.read_csv(_io.StringIO(data.decode("utf-8", errors="replace")), sep=sep)
                total_rows = len(full_df)
            except Exception:
                total_rows = -1
        else:
            df = pd.read_excel(_io.BytesIO(data), nrows=5)
            try:
                xls = pd.ExcelFile(_io.BytesIO(data))
                full_df = pd.read_excel(xls, sheet_name=0)
                total_rows = len(full_df)
            except Exception:
                total_rows = -1
        return {
            "filename": path.name,
            "columns": [str(c) for c in df.columns],
            "rows": total_rows,
            "sample": df.head(5).to_dict(orient="records"),
        }
    except Exception as e:
        print(f"    附件提取失败 {path.name}: {e}")
        return None


def _copy_data_files(attachments: list[Path], year: int, problem_id: str) -> str:
    """将附件文件复制到 data/problems/{year}{problem_id}/，返回目录路径。"""
    target_dir = DATA_DIR / f"{year}{problem_id}"
    target_dir.mkdir(parents=True, exist_ok=True)
    for att in attachments:
        dest = target_dir / att.name
        if not dest.exists():
            shutil.copy2(att, dest)
    return str(target_dir.resolve())


def main():
    existing_ids = set()
    settings = get_settings()
    loader = KnowledgeBaseLoader(settings.kb_root)
    for prob in loader.load_all_problems():
        existing_ids.add((prob.year, prob.problem_id))

    max_num = 0
    for prob in loader.load_all_problems():
        try:
            num = int(prob.id.split("_")[-1])
            max_num = max(max_num, num)
        except Exception:
            pass

    success = 0
    skip = 0
    next_id = max_num + 1

    for year_dir in sorted(DATASET.iterdir()):
        if not year_dir.is_dir():
            continue
        year_match = re.search(r"(\d{4})", year_dir.name)
        if not year_match:
            continue
        year = int(year_match.group(1))
        if year < 2010:
            continue

        print(f"\n--- {year} ---")

        for item in sorted(year_dir.iterdir()):
            problem_id = None
            if item.is_dir():
                pid_match = re.match(r"(\d{4})([A-E])", item.name)
                if pid_match:
                    problem_id = pid_match.group(2)
            else:
                pid_match = re.match(r"([A-E])题", item.name)
                if pid_match:
                    problem_id = pid_match.group(1)

            if not problem_id or problem_id not in "ABCDE":
                continue

            if (year, problem_id) in existing_ids:
                skip += 1
                continue

            # 找问题描述文件 + 附件数据文件
            candidates = []
            attachments = []
            if item.is_dir():
                for f in item.iterdir():
                    if f.suffix.lower() in (".pdf", ".doc", ".docx", ".txt"):
                        if any(kw in f.name for kw in ("附件", "数据", "Data", "data", "format")):
                            continue
                        candidates.append(f)
                    elif f.suffix.lower() in (".xlsx", ".xls", ".csv", ".tsv"):
                        attachments.append(f)
            elif item.suffix.lower() in (".pdf", ".doc", ".docx"):
                candidates.append(item)

            if not candidates:
                print(f"  {year}{problem_id}: 无可识别的问题文件，跳过")
                skip += 1
                continue

            best = max(candidates, key=lambda p: p.stat().st_size)
            text = extract_problem_text(best)
            text = re.sub(r"[^一-鿿　-〿＀-￯ -~\n\r\t。，；：！？\u201c\u201d\u2018\u2019（）【】《》…—\-\+\*\/\=\<\>\(\)\[\]\{\}]", "", text)
            text = re.sub(r"\n{3,}", "\n\n", text)
            text = text.strip()

            cn_chars = sum(1 for c in text if "一" <= c <= "鿿")
            if len(text) < 200 or cn_chars < 3:
                print(f"  {year}{problem_id}: 文本提取质量不足 ({len(text)} chars, {cn_chars} CJK)")
                skip += 1
                continue

            # 提取附件信息
            data_files_info = []
            data_desc_lines = []
            for att in attachments:
                info = _extract_attachment_info(att)
                if info:
                    data_files_info.append(info)
                    data_desc_lines.append(
                        f"附件{len(data_files_info)}: {info['filename']} "
                        f"({info['rows']}行, 列: {', '.join(info['columns'])})"
                    )

            # 复制附件到 data/problems/
            data_files_dir = ""
            if attachments:
                data_files_dir = _copy_data_files(attachments, year, problem_id)
                print(f"  {year}{problem_id}: 复制 {len(attachments)} 个附件到 {data_files_dir}")

            data_description = "; ".join(data_desc_lines) if data_desc_lines else ""

            # 尝试提取标题
            title = f"{year}国赛{problem_id}题"
            first_lines = text.split("\n")
            for line in first_lines[:5]:
                line = line.strip()
                if len(line) > 5 and any(c > "一" for c in line[:10]):
                    if "建模" in line or "题目" in line or "题" in line:
                        title = line[:60]
                        break

            tags = PROBLEM_TYPE_MAP.get(problem_id, ["其他"])

            # 写入 YAML
            prob_id = f"prob_{next_id:03d}"
            next_id += 1

            # 序列化 data_files（YAML 兼容格式）
            data_files_yaml = _json.dumps(data_files_info, ensure_ascii=False, indent=4)
            data_files_yaml_indented = "\n".join("    " + l for l in data_files_yaml.split("\n"))

            yaml_content = f"""problem:
  id: "{prob_id}"
  year: {year}
  competition: "国赛"
  problem_id: "{problem_id}"
  title: "{title}"
  full_text: |
{chr(10).join('    ' + l for l in text[:5000].split(chr(10)))}
  background: ""
  objectives: []
  data_description: "{data_description}"
  data_files: {data_files_yaml_indented}
  deliverables: []
  tags:
    problem_type: {tags}
    difficulty: "medium"
  linked_papers: []
  source_url: ""
"""

            out_dir = settings.kb_root / "problems"
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"{prob_id}.yaml"
            out_path.write_text(yaml_content, encoding="utf-8")

            print(f"  {year}{problem_id}: {title} [{len(text)} chars, {len(data_files_info)} 附件] -> {out_path.name}")
            existing_ids.add((year, problem_id))
            success += 1

    print(f"\n成功: {success}, 跳过: {skip}")


if __name__ == "__main__":
    main()