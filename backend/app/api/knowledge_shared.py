"""知识库路由共享层 — Pydantic 模型 + 检索/文件辅助函数（god-files 拆分 #31）。"""

import re
from pathlib import Path

import yaml
from pydantic import BaseModel

from ..config import get_settings

# ── response models ────────────────────────────────────────────────────


class KBStats(BaseModel):
    methods_count: int = 0
    papers_count: int = 0
    templates_count: int = 0
    problems_count: int = 0
    total: int = 0


class MethodCardSummary(BaseModel):
    id: str
    name: str
    category: list[str]
    applicable_when: list[str]
    typical_scenarios: list[str]


class MethodCardDetail(BaseModel):
    id: str
    name: str
    category: list[str]
    principle: str
    formulas: list[dict]
    applicable_when: list[str]
    not_applicable_when: list[str]
    typical_scenarios: list[str]
    common_mistakes: list[dict]
    code_snippets: list[dict]
    related_cards: list[str]
    related_papers: list[str]


class PaperSummary(BaseModel):
    id: str
    year: int
    competition: str
    problem_id: str
    title: str
    tags: dict
    quality_rating: int
    problem_ref: str = ""


class PaperDetail(BaseModel):
    id: str
    year: int
    competition: str
    problem_id: str
    title: str
    tags: dict
    problem_ref: str = ""
    problem_context: str = ""
    methodology_chain: list[str] = []
    key_formulas: list[dict] = []
    algorithm_outline: list[dict] = []
    assumption_analysis: list[str] = []
    reusable_patterns: list[str] = []
    common_pitfalls: list[dict] = []
    difficulty_level: str = "medium"
    analysis: dict
    model: dict
    evaluation: dict
    source: str
    quality_rating: int


class TemplateSummary(BaseModel):
    id: str
    name: str
    applicable_to: list[str]
    steps_count: int


class TemplateDetail(BaseModel):
    id: str
    name: str
    applicable_to: list[str]
    steps: list[dict]


class ProblemSummary(BaseModel):
    id: str
    year: int
    competition: str
    problem_id: str
    title: str
    tags: dict
    linked_papers_count: int = 0


class ProblemDetail(BaseModel):
    id: str
    year: int
    competition: str
    problem_id: str
    title: str
    full_text: str = ""
    background: str = ""
    objectives: list[str] = []
    data_description: str = ""
    deliverables: list[str] = []
    tags: dict
    linked_papers: list[str] = []
    source_url: str = ""


class SearchResult(BaseModel):
    id: str
    type: str
    name: str = ""
    title: str = ""
    snippet: str
    score: float | None = None


class SearchResponse(BaseModel):
    query: str
    total: int
    results: list[SearchResult]


class ReindexResponse(BaseModel):
    success: bool
    indexed_count: int
    message: str


# ── CRUD response models ─────────────────────────────────────────────


class KnowledgeCrudResponse(BaseModel):
    success: bool
    entry_id: str = ""
    message: str = ""


class KnowledgeUploadJob(BaseModel):
    job_id: str
    status: str  # "processing" | "completed" | "error"
    result: dict | None = None
    error: str | None = None


# ── in-memory job store (upload extraction) ────────────────────────

_extraction_jobs: dict[str, dict] = {}


# ── helpers ─────────────────────────────────────────────────────────


def _get_loader():
    settings = get_settings()
    from ..knowledge.loader import KnowledgeBaseLoader

    return KnowledgeBaseLoader(settings.kb_root)


def _get_retriever():
    """返回进程级共享 retriever 单例（复用 BM25 与 Chroma，避免每请求重建）。"""
    from ..knowledge.retriever import get_shared_retriever

    return get_shared_retriever()


def _get_embedder():
    settings = get_settings()
    from ..knowledge.embedder import KBEmbedder

    return KBEmbedder(
        kb_root=settings.kb_root,
        persist_dir=settings.chroma_dir,
    )


def _find_yaml_file(kb_type: str, entry_id: str) -> Path | None:
    """Scan knowledge_base/{subdir}/**/*.yaml for the file with matching id."""
    settings = get_settings()
    subdir_map = {
        "method": "methods",
        "paper": "papers",
        "template": "templates",
        "problem": "problems",
    }
    key_map = {
        "method": "method_card",
        "paper": "paper",
        "template": "template",
        "problem": "problem",
    }
    subdir = subdir_map.get(kb_type, kb_type)
    top_key = key_map.get(kb_type, "")
    search_dir = settings.kb_root / subdir
    if not search_dir.exists():
        return None
    for yf in search_dir.rglob("*.yaml"):
        try:
            data = yaml.safe_load(yf.read_text(encoding="utf-8"))
            if data and top_key in data and isinstance(data[top_key], dict):
                if data[top_key].get("id") == entry_id:
                    return yf
        except Exception:
            continue
    return None


def _next_id(kb_type: str) -> str:
    """Auto-generate the next sequential ID."""
    settings = get_settings()
    subdir_map = {
        "method": "methods",
        "paper": "papers",
        "template": "templates",
        "problem": "problems",
    }
    prefix_map = {
        "method": "mc_",
        "paper": "paper_",
        "template": "tpl_",
        "problem": "prob_",
    }
    subdir = subdir_map.get(kb_type, kb_type)
    prefix = prefix_map.get(kb_type, "id_")
    search_dir = settings.kb_root / subdir
    existing: list[int] = []
    if search_dir.exists():
        for yf in search_dir.rglob("*.yaml"):
            try:
                data = yaml.safe_load(yf.read_text(encoding="utf-8"))
                if not data:
                    continue
                key_map = {
                    "method": "method_card",
                    "paper": "paper",
                    "template": "template",
                    "problem": "problem",
                }
                top_key = key_map.get(kb_type, "")
                if top_key in data and isinstance(data[top_key], dict):
                    rid = data[top_key].get("id", "")
                    m = re.match(rf"^{re.escape(prefix)}(\d+)$", rid)
                    if m:
                        existing.append(int(m.group(1)))
            except Exception:
                continue
    val = max(existing) + 1 if existing else 1
    return f"{prefix}{val:03d}"


# ── stats ───────────────────────────────────────────────────────────────
