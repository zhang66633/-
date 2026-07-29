"""情景记忆 — 方案完成后的经验积累与召回。

每次 solution 完成:
  1. LLM 生成一条经验摘要（"什么题→用了什么方法→效果如何"）
  2. embed → 存入 ChromaDB collection "episodic_memory"

每次新建 solution:
  1. 用题目描述做向量检索 top_k=3
  2. 召回的经验注入 Orchestrator system prompt 尾部
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from langchain_core.documents import Document

from app.config import get_settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "episodic_memory"

# ── 经验摘要 prompt ─────────────────────────────────────────

EXPERIENCE_PROMPT = """你是一个数学建模经验记录器。根据这次建模任务的完整信息，写一条经验摘要。

## 原始问题
{problem}

## 问题类型
{problem_type}

## 使用的核心方法
从最终论文中提取 2-3 个关键方法

## 最终输出（论文摘要）
{output_preview}

## 规则
1. 一句话格式: "[问题类型] 题目关键字 — 用了XX方法 — 关键发现/教训"
2. 80 字以内
3. 聚焦"下次遇到类似题应该怎么做"的可操作经验
4. 如果这次失败了，记录"XX 方法不适用，因为..."

只输出一条经验摘要:"""


class EpisodicMemory:
    """情景记忆管理器 — 经验写入 + 向量召回。"""

    def __init__(self):
        self._store = None
        self._embeddings = None

    @property
    def embeddings(self):
        """获取与 KBEmbedder 相同的 embedding 函数。"""
        if self._embeddings is None:
            from app.knowledge.embedder import KBEmbedder
            settings = get_settings()
            embedder = KBEmbedder(
                kb_root=settings.kb_root,
                persist_dir=settings.chroma_dir,
            )
            self._embeddings = embedder.embeddings
        return self._embeddings

    @property
    def store(self):
        """懒加载 ChromaDB collection。"""
        if self._store is None:
            from langchain_chroma import Chroma
            settings = get_settings()

            if settings.chroma_http_url:
                # 远程模式
                from urllib.parse import urlparse
                import chromadb
                parsed = urlparse(settings.chroma_http_url)
                client = chromadb.HttpClient(
                    host=parsed.hostname or "localhost",
                    port=parsed.port or 8000,
                )
                self._store = Chroma(
                    client=client,
                    collection_name=COLLECTION_NAME,
                    embedding_function=self.embeddings,
                )
            else:
                # 本地模式
                self._store = Chroma(
                    persist_directory=str(settings.chroma_dir),
                    collection_name=COLLECTION_NAME,
                    embedding_function=self.embeddings,
                )
        return self._store

    # ── 写入经验 ────────────────────────────────────────────

    def save(
        self,
        session_id: str,
        problem_raw: str,
        problem_type: str,
        final_output: str,
    ) -> str | None:
        """从方案结果生成经验摘要并存入向量库。返回经验文本，失败返回 None。"""
        if not self.embeddings:
            logger.warning("情景记忆: embedding 未配置，跳过写入")
            return None

        # LLM 生成经验摘要
        prompt = EXPERIENCE_PROMPT.format(
            problem=problem_raw[:1000],
            problem_type=problem_type or "未知",
            output_preview=final_output[:1500],
        )

        try:
            from app.core.llm.factory import get_llm
            llm = get_llm("analysis")
            response = llm.invoke(prompt)
            experience = str(response.content).strip()
        except Exception as e:
            logger.warning("情景记忆: LLM 摘要生成失败: %s", e)
            return None

        if not experience or len(experience) < 10:
            return None

        # 存入向量库
        try:
            doc = Document(
                page_content=experience,
                metadata={
                    "type": "experience",
                    "session_id": session_id,
                    "problem_type": problem_type,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
            self.store.add_documents([doc])
            logger.info("情景记忆: 经验已保存 — %s", experience[:80])
            return experience
        except Exception as e:
            logger.warning("情景记忆: 向量写入失败: %s", e)
            return None

    # ── 召回经验 ────────────────────────────────────────────

    def recall(
        self,
        query: str,
        problem_type: str = "",
        k: int = 3,
    ) -> list[str]:
        """根据当前题目描述召回相似历史经验。

        Returns:
            经验文本列表（按相似度降序）。
        """
        if not self.embeddings:
            return []

        try:
            # 优先按 problem_type 过滤
            where = None
            if problem_type:
                where = {"problem_type": problem_type}

            docs = self.store.similarity_search(query, k=k, filter=where)

            # 如果类型过滤结果不足，放宽过滤
            if len(docs) < k and where:
                docs_fallback = self.store.similarity_search(query, k=k)
                seen = {d.page_content for d in docs}
                for d in docs_fallback:
                    if d.page_content not in seen and len(docs) < k:
                        docs.append(d)
                        seen.add(d.page_content)

            return [d.page_content for d in docs]

        except Exception as e:
            logger.warning("情景记忆: 召回失败: %s", e)
            return []

    # ── 查询统计 ────────────────────────────────────────────

    def count(self) -> int:
        """已存储的经验总数。"""
        try:
            return self.store._collection.count()
        except Exception:
            return 0
