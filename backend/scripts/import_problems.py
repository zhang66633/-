"""从国赛资料大全导入赛题原文到 knowledge_base/problems/。

处理 PDF + .doc（old Word）+ .docx 格式混合。
"""

import re
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.knowledge.loader import KnowledgeBaseLoader
from app.config import get_settings

DATASET = Path(r"D:\_Documents\2026全国大学生数学建模国赛资料大全\1.历年国赛赛题（1992-2025）")

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
                # 跳过明显是二进制垃圾的行
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


def main():
    existing_ids = set()
    settings = get_settings()
    loader = KnowledgeBaseLoader(settings.kb_root)
    for prob in loader.load_all_problems():
        existing_ids.add((prob.year, prob.problem_id))

    # 获取已有最大 ID 序号
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
        # 提取年份
        year_match = re.search(r"(\d{4})", year_dir.name)
        if not year_match:
            continue
        year = int(year_match.group(1))
        if year < 2010:  # 只处理 2010+ 的题
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

            # 找问题描述文件
            candidates = []
            if item.is_dir():
                for f in item.iterdir():
                    if f.suffix.lower() in (".pdf", ".doc", ".docx", ".txt"):
                        # 跳过数据附件
                        if any(kw in f.name for kw in ("附件", "数据", "Data", "data", "format")):
                            continue
                        candidates.append(f)
            elif item.suffix.lower() in (".pdf", ".doc", ".docx"):
                candidates.append(item)

            if not candidates:
                print(f"  {year}{problem_id}: 无可识别的问题文件，跳过")
                skip += 1
                continue

            # 用最大的文件（通常是完整题目）
            best = max(candidates, key=lambda p: p.stat().st_size)
            text = extract_problem_text(best)
            # 清洗文本：去掉不可打印字符、YAML 冲突字符
            text = re.sub(r"[^一-鿿　-〿＀-￯ -~\n\r\t。，；：！？""''（）【】《》…—\-\+\*\/\=\<\>\(\)\[\]\{\}]", "", text)
            text = re.sub(r"\n{3,}", "\n\n", text)
            text = text.strip()

            cn_chars = sum(1 for c in text if "一" <= c <= "鿿")
            if len(text) < 200 or cn_chars < 3:
            if len(text) < 200 or cn_chars < 3:
                print(f"  {year}{problem_id}: 文本提取质量不足 ({len(text)} chars, {cn_chars} CJK)")
                skip += 1
                continue

            # 尝试提取标题
            title = f"{year}国赛{problem_id}题"
            first_lines = text.split("\n")
            for line in first_lines[:5]:
                line = line.strip()
                if len(line) > 5 and any(c > "\u4e00" for c in line[:10]):
                    if "建模" in line or "题目" in line or "题" in line:
                        title = line[:60]
                        break

            tags = PROBLEM_TYPE_MAP.get(problem_id, ["其他"])

            # 写入 YAML
            prob_id = f"prob_{next_id:03d}"
            next_id += 1
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
  data_description: ""
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

            print(f"  {year}{problem_id}: {title} [{len(text)} chars] -> {out_path.name}")
            existing_ids.add((year, problem_id))
            success += 1

    print(f"\n成功: {success}, 跳过: {skip}")


if __name__ == "__main__":
    main()
