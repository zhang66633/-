# 007 检索链路性能与融合数学修正（发现 #21、#22、#24、#25）

## Status
- **Priority**: P2 · **Effort**: M · **Risk**: MED · **Depends on**: none · **Category**: perf
- **Planned at**: commit 1c03e8b, 2026-08-14

## Context
每次检索全量重解析 KB + 重建 BM25 + 重载 Chroma；每次检索默认额外 3 次 LLM 调用（expansion + HyDE + rerank）；RRF 常量未生效、MMR 双重反转、中文多样性代理失效；索引构建 `_find_source_file` O(D×F)。

## Current state
- `backend/app/knowledge/loader.py:21-47` — 四个 load_all_* 无缓存
- `backend/app/core/nodes.py:208-212`、`api/knowledge_routes.py:180-188` — 每请求新建 `HybridRetriever`
- `backend/app/knowledge/retriever.py:124-137` expansion+hyde 默认开；`214-219` LLM rerank 默认开
- `retriever.py:32` `RRF_K=60` 未使用；`178-181` 把 `k=fetch_k` 传进 `_rrf_fusion` 当 RRF 常量；`208-209` `1.0-score` 反转后 `245-249` 再 `1/(1+d)`；`252-264` Jaccard 对中文近似二值；`query` 参数未用
- `backend/app/knowledge/embedder.py:417-435` — 每个 doc 一次 `rglob` + `safe_load`

## Spec
1. `KnowledgeBaseLoader` 加进程级缓存（按 kb_root 键），`reindex/import` 后显式失效；`HybridRetriever` 提供共享单例（同 `chat_routes.py:46-59` 模式）供 pipeline/search 复用，同钩子失效
2. `_rrf_fusion` 显式 `k_constant=RRF_K`，结果截断独立参数；`_mmr_rerank` 直接用归一化相似度（去掉双重反转），diversity 项改用 embedding 余弦（向量已缓存于 vector store，取 top-k 向量做相似度）或退化为字符 bigram 重叠；使用 `query` 参数
3. 低延迟路径（pipeline retrieve、RAG chat）默认关 `use_query_expansion`/`use_reranker`，`/search` 保留默认开（按 k 大小决定是否 rerank）
4. `_find_source_file` 改为一次遍历建 `{doc_id: path}` 映射复用

## Verification
- [ ] 单测：`_rrf_fusion` 分数随 rank 递减且与 k 截断解耦；`_mmr_rerank` 对相同文档不产生 NaN/负值
- [ ] 手工：同查询两次 `/search`，第二次延迟显著下降（缓存命中）
- [ ] 检索 top-k 顺序变化记录（README 审查注记），不劣化即可

## Implementation notes（实现记录与偏差，2026-08-14 实现时追加）
- §3 行为变更已落地：`HybridRetriever._get_relevant_documents` 默认 `use_query_expansion=False`、`use_reranker=False`（`invoke()` 因此对 pipeline/RAG chat 默认保守）；`knowledge_routes.py` 的 `/search` 显式传 `use_query_expansion=True, use_reranker=True` 保持高精度路径开启。`core/nodes.py`、`chat_routes.py` 未改动（scope 外），其默认行为经 retriever 默认值变化生效。
- 偏差：STRICT SCOPE 对 `knowledge_routes.py` 标注「仅改 `_get_retriever`」，但 §1 要求 reindex 后失效钩子，而 `/reindex` 端点就在该文件——故在同文件 `/reindex` 成功后追加 `invalidate_shared_retriever()`。
- 已知遗留（未改，超出本计划范围）：`knowledge_routes.py` 的手工 CRUD（create/update/delete methods/papers/templates/problems）会写 YAML + 更新索引，但未接失效钩子，可能导致 loader 解析缓存短暂陈旧；建议后续计划补上。
- `_mmr_rerank` 由 `@staticmethod` 改为实例方法（需访问 vector store 取向量）；diversity 优先向量余弦、退化为字符 bigram 重叠，`query` 向量用于修正相关性。
