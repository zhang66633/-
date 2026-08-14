"""YAML knowledge base loader with Pydantic validation."""

import threading
from pathlib import Path

import yaml

from .schemas import MethodCard, Paper, Problem, Template

# ── 进程级缓存：避免每次检索都全量重解析 YAML ─────────────────────────
# 键为 (str(kb_root), kind)；`invalidate_kb_cache()` 在 reindex/import 后清空。
_kb_cache: dict = {}
_kb_cache_lock = threading.Lock()


def invalidate_kb_cache() -> None:
    """清空知识库解析缓存（reindex/import 后由 retriever 单例失效钩子触发）。"""
    with _kb_cache_lock:
        _kb_cache.clear()


class KnowledgeBaseLoader:
    """Load and validate YAML knowledge base files."""

    def __init__(self, kb_root: Path):
        self.kb_root = Path(kb_root)
        self.methods_dir = self.kb_root / "methods"
        self.papers_dir = self.kb_root / "papers"
        self.templates_dir = self.kb_root / "templates"
        self.problems_dir = self.kb_root / "problems"

    def _load_cached(self, kind: str, builder):
        """按 (kb_root, kind) 缓存解析结果，复用已解析的 collection。

        缓存进程级共享、按 kb_root 隔离；`invalidate_kb_cache()` 在 reindex/import
        完成后清空。builder 无参并返回对应类型的列表。
        """
        key = (str(self.kb_root), kind)
        with _kb_cache_lock:
            cached = _kb_cache.get(key)
            if cached is not None:
                return cached
        result = builder()
        with _kb_cache_lock:
            _kb_cache[key] = result
        return result

    def load_all_methods(self) -> list[MethodCard]:
        """Load all method cards from YAML files（进程级缓存，按 kb_root 复用）。"""

        def _build() -> list[MethodCard]:
            cards = []
            for yaml_file in self.methods_dir.rglob("*.yaml"):
                data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
                if data and "method_card" in data:
                    cards.append(MethodCard(**data["method_card"]))
            return cards

        return self._load_cached("methods", _build)

    def load_all_papers(self) -> list[Paper]:
        """Load all structured papers from YAML files（进程级缓存）。"""

        def _build() -> list[Paper]:
            papers = []
            for yaml_file in self.papers_dir.rglob("*.yaml"):
                data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
                if data and "paper" in data:
                    papers.append(Paper(**data["paper"]))
            return papers

        return self._load_cached("papers", _build)

    def load_all_templates(self) -> list[Template]:
        """Load all analysis templates from YAML files（进程级缓存）。"""

        def _build() -> list[Template]:
            templates = []
            for yaml_file in self.templates_dir.rglob("*.yaml"):
                data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
                if data and "template" in data:
                    templates.append(Template(**data["template"]))
            return templates

        return self._load_cached("templates", _build)

    def get_method_by_id(self, card_id: str) -> MethodCard | None:
        """Find a specific method card by ID."""
        for card in self.load_all_methods():
            if card.id == card_id:
                return card
        return None

    def get_methods_by_category(self, category: str) -> list[MethodCard]:
        """Filter method cards by category."""
        return [card for card in self.load_all_methods() if category in card.category]

    def get_papers_by_type(self, problem_type: str) -> list[Paper]:
        """Find papers matching a problem type tag."""
        results = []
        for paper in self.load_all_papers():
            tags = paper.tags
            types = tags.get("problem_type", [])
            if problem_type in types:
                results.append(paper)
        return results

    def get_template_by_id(self, tpl_id: str) -> Template | None:
        """Find a specific template by ID."""
        for tpl in self.load_all_templates():
            if tpl.id == tpl_id:
                return tpl
        return None

    def get_templates_for_type(self, problem_type: str) -> list[Template]:
        """Find templates applicable to a problem type."""
        results = []
        for tpl in self.load_all_templates():
            if problem_type in tpl.applicable_to:
                results.append(tpl)
        return results

    # ── Problem (竞赛真题) ────────────────────────────────────────────

    def load_all_problems(self) -> list[Problem]:
        """Load all competition problems from YAML files（进程级缓存）。"""

        def _build() -> list[Problem]:
            problems = []
            if not self.problems_dir.exists():
                return problems
            for yaml_file in self.problems_dir.rglob("*.yaml"):
                data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
                if data and "problem" in data:
                    problems.append(Problem(**data["problem"]))
            return problems

        return self._load_cached("problems", _build)

    def get_problem_by_id(self, problem_id: str) -> Problem | None:
        """Find a specific problem by ID."""
        for prob in self.load_all_problems():
            if prob.id == problem_id:
                return prob
        return None

    def get_problem_by_key(self, year: int, competition: str, problem_id: str) -> Problem | None:
        """Find a problem by its natural key (year, competition, problem_id)."""
        for prob in self.load_all_problems():
            if (
                prob.year == year
                and prob.competition == competition
                and prob.problem_id == problem_id
            ):
                return prob
        return None

    def get_problems_by_competition(
        self, competition: str, year: int | None = None
    ) -> list[Problem]:
        """Filter problems by competition, optionally by year."""
        results = []
        for prob in self.load_all_problems():
            if prob.competition != competition:
                continue
            if year is not None and prob.year != year:
                continue
            results.append(prob)
        return results

    def get_problems_by_type(self, problem_type: str) -> list[Problem]:
        """Filter problems by problem_type tag."""
        return [
            p for p in self.load_all_problems() if problem_type in p.tags.get("problem_type", [])
        ]

    def get_papers_by_problem(self, problem_ref: str) -> list[Paper]:
        """Find all papers linked to a specific problem."""
        return [p for p in self.load_all_papers() if p.problem_ref == problem_ref]
