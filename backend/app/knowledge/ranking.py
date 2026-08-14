"""检索排序纯函数 — RRF 融合 + MMR 多样性重排 + 字符 bigram 相似度。

从 `retriever.py` 抽出（god-files 拆分 #31 第一刀）：本模块不依赖 Chroma/LLM，
仅依赖 numpy 与 langchain 的 Document 类型，便于单测与复用。
"""

from __future__ import annotations

import numpy as np
from langchain_core.documents import Document

# RRF 融合常数（越大各来源权重越均衡）
RRF_K = 60


def rrf_fusion(
    ranked_lists: list[list[Document]],
    k_constant: int = RRF_K,
    top_n: int | None = None,
) -> list[Document]:
    """Reciprocal Rank Fusion: merge multiple ranked lists.

    score(d) = sum(1 / (k_constant + rank_i(d)))  for each list where d appears.

    Args:
        ranked_lists: Each list is already ranked (best first).
        k_constant: RRF constant (default RRF_K=60).
        top_n: Optional truncation of the fused result, independent of k_constant.
    Returns:
        Documents sorted by RRF score descending, truncated to top_n if given.
    """
    if not ranked_lists:
        return []

    rrf_scores: dict[str, tuple[float, Document]] = {}

    for doc_list in ranked_lists:
        for rank, doc in enumerate(doc_list):
            doc_id = doc.metadata.get("id", doc.page_content[:50])
            rrf = 1.0 / (k_constant + rank + 1)
            if doc_id in rrf_scores:
                prev_score, _ = rrf_scores[doc_id]
                rrf_scores[doc_id] = (prev_score + rrf, doc)
            else:
                rrf_scores[doc_id] = (rrf, doc)

    # Sort by RRF score descending
    sorted_items = sorted(rrf_scores.values(), key=lambda x: x[0], reverse=True)
    result = []
    for rrf_score, doc in sorted_items:
        doc.metadata["score"] = round(rrf_score, 6)
        result.append(doc)

    if top_n is not None:
        result = result[:top_n]

    return result


def char_bigrams(text: str) -> set[str]:
    """字符 bigram 集合（中文无空格时比词级 Jaccard 更有效）。"""
    text = (text or "").lower()
    return {text[i : i + 2] for i in range(len(text) - 1)}


def char_bigram_similarity_matrix(docs: list[Document]) -> np.ndarray:
    """字符 bigram 重叠的 pairwise 相似度矩阵（MMR diversity 兜底）。"""
    n = len(docs)
    sets = [char_bigrams(d.page_content) for d in docs]
    pairwise = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(i + 1, n):
            si, sj = sets[i], sets[j]
            if si and sj:
                v = len(si & sj) / len(si | sj)
                pairwise[i, j] = pairwise[j, i] = v
    return pairwise


def mmr_rerank(
    query: str,
    scored_docs: list[tuple[Document, float]],
    k: int = 5,
    lam: float = 0.5,
    doc_embeddings: np.ndarray | None = None,
    query_embedding: np.ndarray | None = None,
) -> list[Document]:
    """Maximum Marginal Relevance reranking（纯函数版）。

    lam=1.0 → pure relevance;  lam=0.0 → pure diversity.

    入参 `score` 已是归一化相似度 [0,1]（调用侧不做 1.0-score 反转，本函数也不
    再反转）。diversity 项优先用传入的文档向量余弦相似度；没有向量时退化为
    字符 bigram 重叠（对中文更友好）。`query_embedding` 可用时用它修正相关性，
    使 `query` 参数真正参与排序。
    """
    if not scored_docs:
        return []

    docs = [d for d, _ in scored_docs]
    n = len(docs)

    # 归一化相似度直接使用（无双重反转）
    sims = np.array([s for _, s in scored_docs], dtype=np.float64)
    sims = np.clip(sims, 0.0, 1.0)
    if sims.max() > 0:
        sims = sims / (sims.max() + 1e-8)

    # 文档向量（可用时）→ 余弦 diversity；不可用 → 字符 bigram 重叠
    if doc_embeddings is not None and doc_embeddings.shape[0] == n and doc_embeddings.shape[1] > 0:
        emb = doc_embeddings / np.maximum(
            np.linalg.norm(doc_embeddings, axis=1, keepdims=True), 1e-8
        )
        pairwise = emb @ emb.T
        np.fill_diagonal(pairwise, 0.0)
        pairwise = np.clip(pairwise, -1.0, 1.0)

        # 用 query 向量修正相关性（query-doc 余弦）
        if query_embedding is not None and query_embedding.size > 0:
            qvec = query_embedding / (np.linalg.norm(query_embedding) + 1e-8)
            qrel = emb @ qvec
            sims = 0.5 * sims + 0.5 * np.clip(qrel, 0.0, 1.0)
            sims = sims / (sims.max() + 1e-8)
    else:
        pairwise = char_bigram_similarity_matrix(docs)

    selected: list[int] = []
    remaining = list(range(n))

    for _ in range(min(k, n)):
        if not remaining:
            break

        if not selected:
            # First pick: highest relevance
            best = max(remaining, key=lambda j: sims[j])
        else:
            # MMR: λ*relevance - (1-λ)*max_similarity_to_selected
            def mmr_score(j: int) -> float:
                rel = sims[j]
                div_penalty = max(pairwise[j, s] for s in selected)
                return lam * rel - (1.0 - lam) * div_penalty

            best = max(remaining, key=mmr_score)

        selected.append(best)
        remaining.remove(best)

    result = []
    for idx in selected:
        doc = docs[idx]
        doc.metadata["score"] = round(float(sims[idx]), 4)
        result.append(doc)
    return result
