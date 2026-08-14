"""LLM-based reranker for retrieved documents.

When the initial retriever returns more candidates than needed (fetch_k > k),
the LLMReranker uses a lightweight scoring prompt to reorder them by relevance
before the final top-k selection.

Design note: this is a quality enhancer, not a replacement for the retriever.
The retriever handles breadth (k → fetch_k); the reranker handles depth
(precision → top_k).
"""

from __future__ import annotations

import json
import re

from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

RERANK_SYSTEM = """你是一个文档相关性评估助手。你需要评估每篇文档与用户问题的相关性。

评分标准 (1-5):
- 5: 高度相关，文档直接解答或覆盖了问题核心
- 4: 相关，文档提供了有用的参考信息
- 3: 部分相关，文档涉及相关领域但不够聚焦
- 2: 弱相关，只有表面关联
- 1: 无关，文档与问题没有实质关系

请严格返回 JSON 数组格式:
[{"index": 0, "score": 4, "reason": "简述理由(不超过20字)"}, ...]

只返回 JSON，不要额外解释。"""

RERANK_HUMAN_TEMPLATE = """用户问题: {query}

评估以下文档与问题的相关性:

{documents}"""


class LLMReranker:
    """Use an LLM to score and rerank a list of candidate Documents."""

    def __init__(
        self,
        llm: BaseChatModel,
        batch_size: int = 10,
        max_doc_chars: int = 600,
    ):
        """
        Args:
            llm:            Chat model used for scoring.
            batch_size:     Max documents per scoring batch.
            max_doc_chars:  Truncate each document's content to this length.
        """
        self.llm = llm
        self.batch_size = batch_size
        self.max_doc_chars = max_doc_chars

    # ── public API ─────────────────────────────────────────────────

    def rerank(
        self,
        query: str,
        documents: list[Document],
        top_k: int = 5,
    ) -> list[Document]:
        """Score and rerank documents by relevance to the query.

        Returns the top_k most relevant documents, each with metadata["score"]
        and metadata["rerank_reason"] populated.
        """
        if not documents:
            return []

        if len(documents) <= top_k:
            # No reranking needed — just stamp default scores
            for d in documents:
                d.metadata.setdefault("score", 3.0)
            return documents

        # Score in batches, then merge
        all_scores: dict[int, tuple[float, str]] = {}
        for batch_start in range(0, len(documents), self.batch_size):
            batch = documents[batch_start : batch_start + self.batch_size]
            scores = self._score_batch(query, batch, offset=batch_start)
            all_scores.update(scores)

        # Sort by score descending
        ranked = sorted(
            enumerate(documents),
            key=lambda t: all_scores.get(t[0], (0.0, ""))[0],
            reverse=True,
        )

        # Stamp metadata and return top_k
        result = []
        for idx, doc in ranked[:top_k]:
            score, reason = all_scores.get(idx, (0.0, ""))
            doc.metadata["score"] = round(score, 2)
            if reason:
                doc.metadata["rerank_reason"] = reason
            result.append(doc)

        return result

    # ── internals ──────────────────────────────────────────────────

    def _score_batch(
        self, query: str, batch: list[Document], offset: int = 0
    ) -> dict[int, tuple[float, str]]:
        """Ask the LLM to score one batch of documents."""
        doc_texts = []
        for i, doc in enumerate(batch):
            content = doc.page_content[: self.max_doc_chars]
            if len(doc.page_content) > self.max_doc_chars:
                content += "..."
            doc_texts.append(
                f"文档 [{i + offset}]: {content}\n  类型: {doc.metadata.get('type', 'unknown')}"
            )

        human_msg = RERANK_HUMAN_TEMPLATE.format(
            query=query,
            documents="\n\n".join(doc_texts),
        )

        try:
            response = self.llm.invoke(
                [
                    SystemMessage(content=RERANK_SYSTEM),
                    HumanMessage(content=human_msg),
                ]
            )
            return self._parse_scores(str(response.content), offset=offset)
        except Exception:
            # On failure, return neutral scores
            return {i + offset: (3.0, "评分失败") for i in range(len(batch))}

    @staticmethod
    def _parse_scores(text: str, offset: int = 0) -> dict[int, tuple[float, str]]:
        """Extract scoring JSON from LLM output (handles markdown fences)."""
        # Strip markdown code fences if present
        json_match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
        if json_match:
            text = json_match.group(1)

        # Try to find a JSON array
        array_match = re.search(r"\[.*\]", text, re.DOTALL)
        if not array_match:
            return {}

        try:
            parsed = json.loads(array_match.group(0))
        except json.JSONDecodeError:
            return {}

        scores: dict[int, tuple[float, str]] = {}
        for item in parsed:
            idx = int(item.get("index", -1))
            score = float(item.get("score", 3))
            reason = str(item.get("reason", ""))
            # Clamp to valid range
            score = max(1.0, min(5.0, score))
            scores[idx] = (score, reason)

        return scores


def create_reranker(
    llm: BaseChatModel,
    batch_size: int = 10,
) -> LLMReranker:
    """Convenience factory for creating a reranker."""
    return LLMReranker(llm=llm, batch_size=batch_size)
