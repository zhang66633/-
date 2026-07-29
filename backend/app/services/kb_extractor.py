"""知识库提取器 — PDF/Markdown 文本提取 → LLM 结构化 → YAML。

用于批量导入论文和方法卡片。LLM 负责从非结构化文本中提取
规范字段，人工审核后入库。
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from pathlib import Path
from typing import Optional

import yaml

from app.config import get_settings
from app.core.llm.factory import get_llm

logger = logging.getLogger(__name__)

# ── LLM 提取 Prompt ──────────────────────────────────────────

EXTRACT_PAPER_PROMPT = """你是一个数学建模论文解析器。根据以下论文文本，提取结构化信息。

论文文本:
```
{text}
```

返回严格的 JSON（不要 Markdown 代码块标记），格式:
{{
  "title": "论文标题",
  "year": 2023,
  "competition": "国赛",
  "problem_id": "C",
  "tags": {{
    "problem_type": ["优化"],
    "core_models": ["线性规划"],
    "techniques": ["灵敏度分析"]
  }},
  "analysis": {{
    "problem_summary": "一句话概括问题本质",
    "key_assumptions": ["假设1", "假设2"],
    "objective": "优化/分析目标",
    "constraints": "主要约束"
  }},
  "model": {{
    "approach": "建模思路概述",
    "innovation": "创新点",
    "solution_method": "求解算法"
  }},
  "evaluation": {{
    "strengths": ["优点1"],
    "weaknesses": ["不足1"],
    "lessons": "可以学到什么"
  }},
  "quality_rating": 4
}}

规则:
- year 必须是整数，competition 只能是 国赛/美赛/研赛/华中赛/校赛
- 如果某字段无法从文本中确定，用空字符串或空列表
- 只返回 JSON，不要任何其他文字"""

EXTRACT_METHOD_PROMPT = """你是一个数学建模知识工程师。从以下文本中提取方法卡片的结构化信息。

文本:
```
{text}
```

返回严格的 JSON:
{{
  "name": "方法名（中文）",
  "name_en": "English Name",
  "category": ["分类1", "分类2"],
  "principle": "核心原理（100-300字）",
  "formulas": [{{"name": "公式名", "latex": "$$...$$", "description": "说明"}}],
  "applicable_when": ["适用条件1", "适用条件2"],
  "not_applicable_when": ["不适用条件"],
  "typical_scenarios": ["典型场景1"],
  "common_mistakes": [{{"mistake": "误用描述", "solution": "正确做法"}}],
  "code_snippets": [{{"language": "python", "description": "说明", "code": "..."}}],
  "difficulty": 3,
  "quality_rating": 3
}}

规则:
- category 从以下选：优化/预测/评价/统计/图论/微分方程/机器学习/数值方法/排队论/博弈论
- difficulty 1-5: 1入门 3中等 5高级
- 只返回 JSON，不要任何其他文字"""


class KBExtractor:
    """知识库提取器：PDF 文本提取 + LLM 结构化。"""

    def __init__(self):
        settings = get_settings()
        self.papers_dir = settings.kb_root / "papers"
        self.methods_dir = settings.kb_root / "methods"
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            # 优先用 env 里的 key（批量脚本不走前端 apikeys 页面）
            settings = get_settings()
            api_config = {"key": settings.openai_api_key, "provider": "openai"}
            if settings.deepseek_base_url:
                api_config["base_url"] = settings.deepseek_base_url
            self._llm = get_llm("analysis", api_key_config=api_config)
        return self._llm

    # ── PDF 文本提取 ────────────────────────────────────────

    @staticmethod
    def extract_pdf_text(data: bytes, max_chars: int = 12000) -> str:
        """从 PDF 二进制数据提取纯文本。

        策略: PyMuPDF → pdfplumber → OCR（扫描版兜底）
        """
        text = ""
        # 1) PyMuPDF（文本型 PDF）
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=data, filetype="pdf")
            pages = []
            for page in doc:
                t = page.get_text()
                if t.strip():
                    pages.append(t)
            doc.close()
            text = "\n\n".join(pages)
        except Exception:
            pass

        # 2) pdfplumber（表格密集的 PDF）
        if not text.strip():
            try:
                import pdfplumber
                import io
                with pdfplumber.open(io.BytesIO(data)) as pdf:
                    pages = [p.extract_text() or "" for p in pdf.pages]
                text = "\n\n".join(pages)
            except Exception:
                pass

        # 3) OCR 兜底（扫描版 PDF，无文本层）
        if not text.strip():
            try:
                from rapidocr_onnxruntime import RapidOCR
                import fitz
                ocr = RapidOCR()
                doc = fitz.open(stream=data, filetype="pdf")
                ocr_pages = []
                for page in doc:
                    # 渲染为图片
                    pix = page.get_pixmap(dpi=200)
                    img_bytes = pix.tobytes("png")
                    result, _ = ocr(img_bytes)
                    if result:
                        lines = []
                        for entry in result:
                            lines.append(entry[1])  # entry = (box, text, confidence)
                        ocr_pages.append(" ".join(lines))
                doc.close()
                text = "\n\n".join(ocr_pages)
                if text.strip():
                    print(f"    [OCR] 扫描版 PDF，识别 {len(text)} 字符")
            except Exception:
                pass

        text = (text or "").strip()
        if len(text) > max_chars:
            # 取前中后各 1/3，保留结构完整性
            third = max_chars // 3
            text = text[:third] + "\n…(省略中间部分)…\n" + text[-third:]
        return text

    # ── LLM 结构化提取 ─────────────────────────────────────

    def extract_paper(self, text: str, filename: str = "") -> dict:
        """从文本中提取论文结构化信息。返回 dict 含 status 和 data/error。"""
        if not text.strip():
            return {"status": "error", "error": "文本为空"}

        prompt = EXTRACT_PAPER_PROMPT.format(text=text[:10000])

        try:
            response = self.llm.invoke(prompt)
            raw = str(response.content).strip()
            # 去掉可能的 Markdown 代码块
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
            data = json.loads(raw)

            # 生成唯一 ID
            year = data.get("year", 0)
            comp = data.get("competition", "未知")
            pid = data.get("problem_id", "X")
            safe_name = re.sub(r"[^\w]", "_", filename.rsplit(".", 1)[0] or "imported")
            paper_id = f"paper_{year}_{comp}_{pid}_{safe_name[:20]}"

            paper_yaml = {
                "paper": {
                    "id": paper_id,
                    "year": year,
                    "competition": comp,
                    "problem_id": pid,
                    "title": data.get("title", ""),
                    "tags": data.get("tags", {}),
                    "analysis": data.get("analysis", {}),
                    "model": data.get("model", {}),
                    "evaluation": data.get("evaluation", {}),
                    "quality_rating": max(data.get("quality_rating", 3) or 3, 1),
                    "source": filename,
                }
            }
            return {"status": "ok", "data": paper_yaml, "paper_id": paper_id}

        except json.JSONDecodeError as e:
            logger.warning("LLM 返回非 JSON: %s", str(e)[:200])
            return {"status": "error", "error": f"LLM 输出解析失败: {e}"}
        except Exception as e:
            logger.exception("论文提取失败")
            return {"status": "error", "error": str(e)}

    def extract_method(self, text: str, filename: str = "") -> dict:
        """从文本中提取方法卡片结构化信息。"""
        if not text.strip():
            return {"status": "error", "error": "文本为空"}

        prompt = EXTRACT_METHOD_PROMPT.format(text=text[:8000])

        try:
            response = self.llm.invoke(prompt)
            raw = str(response.content).strip()
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
            data = json.loads(raw)

            # 生成 ID
            existing = self._next_method_ids()
            next_id = f"mc_{len(existing) + 1:03d}"

            # 解析 category（可能为逗号分隔字符串或列表）
            cat_raw = data.get("category", [])
            if isinstance(cat_raw, str):
                categories = [c.strip() for c in cat_raw.split(",") if c.strip()]
            else:
                categories = cat_raw

            method_yaml = {
                "method_card": {
                    "id": next_id,
                    "name": data.get("name", ""),
                    "name_en": data.get("name_en", ""),
                    "category": categories,
                    "principle": data.get("principle", ""),
                    "formulas": data.get("formulas", []),
                    "applicable_when": data.get("applicable_when", []),
                    "not_applicable_when": data.get("not_applicable_when", []),
                    "typical_scenarios": data.get("typical_scenarios", []),
                    "common_mistakes": data.get("common_mistakes", []),
                    "code_snippets": data.get("code_snippets", []),
                    "related_cards": data.get("related_cards", []),
                    "related_papers": data.get("related_papers", []),
                    "difficulty": data.get("difficulty", 3),
                    "quality_rating": data.get("quality_rating", 3),
                }
            }
            return {"status": "ok", "data": method_yaml, "method_id": next_id}

        except json.JSONDecodeError as e:
            return {"status": "error", "error": f"LLM 输出解析失败: {e}"}
        except Exception as e:
            logger.exception("方法提取失败")
            return {"status": "error", "error": str(e)}

    # ── YAML 写入 ──────────────────────────────────────────

    def write_paper(self, paper_yaml: dict) -> Path:
        """将论文 YAML 写入 knowledge_base/papers/。"""
        paper = paper_yaml["paper"]
        comp = paper.get("competition", "其他")
        comp_dir = self.papers_dir / comp
        comp_dir.mkdir(parents=True, exist_ok=True)

        fname = f"{paper['id']}.yaml"
        path = comp_dir / fname
        path.write_text(
            yaml.dump(paper_yaml, allow_unicode=True, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )
        return path

    def write_method(self, method_yaml: dict, category: str = "") -> Path:
        """将方法卡片 YAML 写入 knowledge_base/methods/。"""
        card = method_yaml["method_card"]
        cat = category or (card.get("category", ["其他"])[0] if card.get("category") else "其他")
        cat_dir = self.methods_dir / cat
        cat_dir.mkdir(parents=True, exist_ok=True)

        fname = f"{card['id']}.yaml"
        path = cat_dir / fname
        path.write_text(
            yaml.dump(method_yaml, allow_unicode=True, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )
        return path

    def embed_new(self, yaml_path: Path) -> int:
        """将新 YAML 文件加入向量索引。返回索引文档数。"""
        from app.knowledge.embedder import KBEmbedder
        settings = get_settings()
        embedder = KBEmbedder(
            kb_root=settings.kb_root,
            persist_dir=settings.chroma_dir,
        )
        return embedder.add_document(yaml_path)

    def _next_method_ids(self) -> list[str]:
        """获取已有方法卡片 ID 列表，用于生成新 ID。"""
        from app.knowledge.loader import KnowledgeBaseLoader
        settings = get_settings()
        loader = KnowledgeBaseLoader(settings.kb_root)
        return [c.id for c in loader.load_all_methods()]
