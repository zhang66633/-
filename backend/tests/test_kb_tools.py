"""KB 工具回归测试 — HybridRetriever 适配（协议 v2.1 配套修复）。

覆盖:
  - get_analysis_template 用 invoke(metadata_filter=...) 而非旧版 search_kwargs 字段
  - KB 路径与 settings.kb_root / chroma_dir 一致（不再硬编码 data/knowledge_base）
"""

from __future__ import annotations

import app.tools.kb_tools as kb


def test_get_analysis_template_uses_metadata_filter(monkeypatch):
    """回归：不能用 search_kwargs（HybridRetriever 是 pydantic 模型，无该字段）。"""
    class FakeRetriever:
        def __init__(self):
            self.calls: list[tuple] = []

        def invoke(self, query: str, **kwargs):
            self.calls.append((query, kwargs))
            return []

    fake = FakeRetriever()
    monkeypatch.setattr(kb, "get_retriever", lambda: fake)

    tool = kb.GetAnalysisTemplateTool()
    out = tool._run("评价类问题模板")

    assert "未找到相关模板" in out
    # 关键：invoke 走 metadata_filter 参数，而不是给 retriever 赋 search_kwargs 字段
    assert fake.calls[0][1] == {"metadata_filter": {"type": "template"}}


def test_method_and_paper_tools_filter(monkeypatch):
    """三个工具统一走 metadata_filter，type 值与索引一致。"""
    class FakeRetriever:
        def __init__(self):
            self.calls: list[tuple] = []

        def invoke(self, query: str, **kwargs):
            self.calls.append(kwargs)
            return []

    fake = FakeRetriever()
    monkeypatch.setattr(kb, "get_retriever", lambda: fake)

    kb.SearchMethodCardsTool()._run("线性规划")
    kb.SearchSimilarPapersTool()._run("2023 国赛 A 题")

    assert fake.calls[0] == {"metadata_filter": {"type": "method_card"}}
    assert fake.calls[1] == {"metadata_filter": {"type": "paper"}}


def test_resolve_kb_paths_matches_settings(monkeypatch):
    """回归：KB 路径与 settings 一致（真实库在 settings.kb_root，不是 data/knowledge_base）。"""
    from app.config import get_settings

    monkeypatch.setattr(kb, "_KB_ROOT", None)
    monkeypatch.setattr(kb, "_PERSIST_DIR", None)

    settings = get_settings()
    root, persist = kb._resolve_kb_paths()

    assert root == settings.kb_root
    assert persist == settings.chroma_dir
