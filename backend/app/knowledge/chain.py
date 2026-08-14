"""RAG Chains: retrieval → format → inject → generate.

Provides:
  - create_rag_chain()            Standard LCEL RAG pipeline
  - create_structured_rag_chain() RAG with structured output
  - format_docs()                 Document list → LLM-friendly context string
  - format_kb_context()           Full KB context from AgentState fields
"""

from __future__ import annotations

from operator import itemgetter

from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import (
    RunnableSerializable,
)

# ── document formatting ────────────────────────────────────────────────


def _trim_doc(doc: Document, max_len: int = 1000) -> str:
    content = doc.page_content
    if len(content) > max_len:
        content = content[:max_len] + "\n... [已截断]"
    return content


def format_docs(docs: list[Document]) -> str:
    """Render retrieved documents as a formatted context block for the LLM."""
    if not docs:
        return "（知识库中未找到相关参考资料）"

    type_labels = {
        "method_card": "方法卡片",
        "paper": "真题论文",
        "template": "分析框架",
        "problem": "竞赛真题",
    }

    parts: list[str] = []
    for i, doc in enumerate(docs, start=1):
        meta = doc.metadata
        label = type_labels.get(meta.get("type", ""), "参考资料")
        name = meta.get("name") or meta.get("title") or "未知"
        score = meta.get("score")
        score_str = f" [相关性: {score:.2f}]" if score is not None else ""

        parts.append(f"### 参考 {i}: [{label}] {name}{score_str}\n\n{_trim_doc(doc)}\n")

    return "\n".join(parts)


def format_kb_context(
    kb_methods: list[dict] | None = None,
    kb_papers: list[dict] | None = None,
    kb_templates: list[dict] | None = None,
    kb_problems: list[dict] | None = None,
) -> str:
    """Build a combined KB context string from AgentState fields.

    Use this inside LangGraph nodes to inject KB results into prompts.
    """
    sections: list[str] = []

    if kb_problems:
        problems_text = "\n".join(
            f"- **{p.get('title', '?')}** [{p.get('id', '?')}] ({p.get('year', '?')} {p.get('competition', '?')} {p.get('problem_id', '?')}): {p.get('page_content', '') or p.get('background', '')[:200]}"
            for p in kb_problems
        )
        sections.append(f"## 相关竞赛真题\n{problems_text}")

    if kb_methods:
        methods_text = "\n".join(
            f"- **{m.get('name', '?')}** [{m.get('id', '?')}]: {m.get('page_content', '') or m.get('principle', '')[:200]}"
            for m in kb_methods
        )
        sections.append(f"## 推荐方法\n{methods_text}")

    if kb_papers:
        papers_text = "\n".join(
            f"- **{p.get('title', '?')}** [{p.get('id', '?')}] ({p.get('year', '?')} {p.get('competition', '?')}): {p.get('page_content', '') or p.get('approach', '')[:200]}"
            for p in kb_papers
        )
        sections.append(f"## 相似真题论文\n{papers_text}")

    if kb_templates:
        templates_text = "\n".join(
            f"- **{t.get('name', '?')}** [{t.get('id', '?')}]: {t.get('page_content', '') or t.get('name', '')[:200]}"
            for t in kb_templates
        )
        sections.append(f"## 分析框架\n{templates_text}")

    if not sections:
        return "（本次未从知识库检索到相关内容）"

    sections.insert(0, "## 知识库参考上下文")
    return "\n\n".join(sections)


# ── RAG chain builders ─────────────────────────────────────────────────


def create_rag_chain(
    llm: BaseChatModel,
    retriever: BaseRetriever,
    prompt_template: ChatPromptTemplate,
) -> RunnableSerializable:
    """Build a standard RAG chain: retrieve → format → prompt → generate.

    Args:
        llm:              The chat model for generation.
        retriever:        Any BaseRetriever (HybridRetriever works directly).
        prompt_template:  A ChatPromptTemplate with {context} and {question} slots.

    Returns a Runnable that accepts a question string and returns the LLM response.
    """
    return (
        {
            "context": itemgetter("question") | retriever | format_docs,
            "question": itemgetter("question"),
        }
        | prompt_template
        | llm
        | StrOutputParser()
    )


def create_rag_with_structured_output(
    llm: BaseChatModel,
    retriever: BaseRetriever,
    prompt_template: ChatPromptTemplate,
    output_schema: type,
) -> RunnableSerializable:
    """Build a RAG chain that returns structured (Pydantic) output.

    Args:
        llm:              The chat model (must support with_structured_output).
        retriever:        Any BaseRetriever.
        prompt_template:  ChatPromptTemplate with {context} and {question}.
        output_schema:    Pydantic model class for structured output.

    Returns a Runnable[question → PydanticModel].
    """
    structured_llm = llm.with_structured_output(output_schema)
    return (
        {
            "context": itemgetter("question") | retriever | format_docs,
            "question": itemgetter("question"),
        }
        | prompt_template
        | structured_llm
    )


def create_kb_context_chain(
    llm: BaseChatModel,
    prompt_template: ChatPromptTemplate,
) -> RunnableSerializable:
    """Build a chain where KB context is already embedded in the input.

    For use inside LangGraph nodes where context is assembled from AgentState
    before being passed here.  Expects {"context": ..., "question": ..., ...}.

    Args:
        llm:              The chat model.
        prompt_template:  ChatPromptTemplate with {context} and other slots.

    Returns a Runnable that accepts a dict with "context" and generates a response.
    """
    return prompt_template | llm | StrOutputParser()
