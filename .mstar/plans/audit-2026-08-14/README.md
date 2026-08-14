# Audit Report — math_agent @ a827024 (2026-08-14)

全面代码审查：FastAPI + LangGraph 后端（`backend/app/**`）+ Vue3 前端（`frontend/src/**`）+ 部署配置与文档。
方法：4 路并行只读类别扫描（安全 / 后端正确性·性能·测试 / 前端正确性·安全·性能 / 技术债·依赖·DX·文档·方向）+ 主审逐条打开引用文件核验（vet）。
未审计范围：`_plugins/`（DSH 插件源码，非本项目代码）、`node_modules/`、`backend/data/`（运行时数据）、LLM 生成质量与 prompt 内容、Python 依赖的 pip-audit（本机未安装）、真实网络环境下的利用验证（未运行任何攻击）。

## Findings

| # | Finding | Category | Impact | Effort | Risk | Confidence | Evidence |
|---|---------|----------|--------|--------|------|------------|----------|
| 1 | 路径穿越：`/api/task_files/../apikeys.json` 未鉴权读取明文 API key 与全部聊天记录 | security | HIGH | XS | LOW | HIGH | `backend/app/api/files.py:15,114-127` |
| 2 | 论文导出打印窗口 XSS：`RAW_MD` 注入 `<script>` 逃逸 + marked 输出无 DOMPurify 直入同源窗口 | security | HIGH | S | MED | HIGH | `frontend/src/utils/exportPaper.ts:133,140-146,187-189` |
| 3 | subprocess 沙箱在 Windows 无有效隔离（默认后端）：rlimit 不生效、socket 补丁可绕过、可读 `.env` | security | HIGH | M | MED | HIGH | `backend/app/sandbox/executor.py:29-44,235-243`; `backend/app/config.py:79` |
| 4 | 会话/任务/文件接口零鉴权零属主：`/api/conversations/*` 全部可匿名列/读/删 | security | HIGH | S | MED | HIGH | `backend/app/api/session_routes.py:52-152`; `tasks.py:200-202`; `files.py:42,83` |
| 5 | 暴露面配置：`.env` HOST=0.0.0.0 + DEBUG=true（异常详情回传客户端），各启动路径绑定不一致 | security | MED | XS | LOW | HIGH | `backend/app/main.py:119-127`; `config.py:28-30`; `backend/.env` |
| 6 | OAuth 登录无 `state` 参数 → login CSRF | security | MED | XS | LOW | HIGH | `backend/app/api/router.py:43-97` |
| 7 | API Key 验证接口 SSRF：用户可控 `base_url` 触发服务端任意内网 POST | security | MED | XS | LOW | MED | `backend/app/api/apikeys.py:139-182` |
| 8 | JWT 存 localStorage + WS token 走 URL query + 登出不清理持久化会话（跨账号泄露） | security | MED | S | MED | HIGH | `frontend/src/stores/auth.ts:12,83-104`; `task.ts:183-185`; `chatSession.ts:262-268` |
| 9 | 验证 FAIL 回退进入 modeling 死循环直至 recursion_limit=50（烧 ~50 次建模 LLM 调用后任务报错） | bug | HIGH | S | MED | HIGH | `backend/app/core/nodes.py:466-532,896-901`; `router.py:39-52` |
| 10 | 导出节点 except 内 `logger` 未定义 → NameError 升级为任务失败 | bug | MED | XS | LOW | HIGH | `backend/app/core/nodes.py:1293` |
| 11 | BKT 衰减每次 profile 拉取重复乘算 → 掌握度指数崩塌至 0 | bug | MED | S | LOW | HIGH | `backend/app/learning/mastery_tracker.py:91-119`; `api/profile_routes.py:89` |
| 12 | 任务取消是装饰性的：cancel 事件管线内从不检查，取消后仍烧完全部 token | bug | MED | M | MED | HIGH | `backend/app/core/nodes.py:66-73`; `api/tasks.py:287-322` |
| 13 | 工作记忆异步重写在无事件循环线程静默失败（solution-via-chat 路径 problem_doc 永不更新） | bug | MED | S | LOW | MED | `backend/app/core/nodes.py:87-90` |
| 14 | 代码块「复制」按钮 onclick 被 DOMPurify 剥离 → 按钮失效 | bug | LOW | XS | LOW | HIGH | `frontend/src/utils/markdown.ts:132-135,180` |
| 15 | SSE 断连自动重连是死代码（无调用者、handleUserSend 从不抛错） | bug | LOW | S | LOW | HIGH | `frontend/src/composables/useStreamChat.ts:204-223` |
| 16 | 流式请求无 unmount 清理 + abortController 单引用跨发送竞态 | bug | MED | M | MED | HIGH | `frontend/src/composables/useStreamChat.ts` |
| 17 | `renderMarkdownStreaming` 模块级节流状态跨组件互串 | bug | LOW | XS | LOW | HIGH | `frontend/src/utils/markdown.ts:230-244` |
| 18 | 知识库「保存」按钮是零 API 调用的空操作、无条件报成功 | bug | MED | S | LOW | MED | `frontend/src/pages/knowledge/index.vue:778-798,841-846` |
| 19 | KaTeX MathML 被 DOMPurify 剥离（a11y 损失）；heading/table 渲染器丢失内联格式 | bug | LOW | S | LOW | MED | `frontend/src/utils/markdown.ts:142-158,180` |
| 20 | SSE 解析器按 `\n\n` 切帧 + 单行 data: 假设（当前后端兼容，健壮性风险） | bug | LOW | S | LOW | MED | `frontend/src/apis/chatApi.ts:150-156` |
| 21 | 每次检索全量重解析 KB + 重建 BM25 + 重载 Chroma（pipeline/search 未复用缓存） | perf | MED | S | LOW | HIGH | `backend/app/knowledge/loader.py:21-47`; `core/nodes.py:208-212`; `api/knowledge_routes.py:180-188` |
| 22 | 每次检索默认额外 3 次 LLM 调用（query expansion + HyDE + rerank）且无缓存 | perf | MED | M | MED | HIGH | `backend/app/knowledge/retriever.py:124-137,214-219` |
| 23 | SQLite 会话存储每调用新建连接且不显式关闭 | perf | MED | M | LOW | HIGH | `backend/app/services/sqlite_session_store.py:81-87` |
| 24 | RRF_K 常量未用 / MMR 双重反转 / 中文多样性代理失效 | perf | MED | M | MED | MED | `backend/app/knowledge/retriever.py:32,178-181,208-209,245-264` |
| 25 | 索引构建 `_find_source_file` 为 O(D×F) 全量重复 YAML 解析 | perf | LOW | S | LOW | HIGH | `backend/app/knowledge/embedder.py:417-435` |
| 26 | 零自动化测试 + 无 CI + biome 未接线 → 无任何一条验证命令（前置阻塞项） | tests | HIGH | L | LOW | HIGH | `backend/pyproject.toml:46-51`（pytest 未用）; `frontend/package.json:6-10` |
| 27 | 依赖无锁文件 + 全开放下限 + alpha 依赖 + 双 lockfile + 34 个高危 advisory（经未使用的 render-jupyter-notebook-vue） | deps | MED | S | LOW | HIGH | `backend/pyproject.toml:8-44`; `frontend/package.json:11-30` |
| 28 | docker-compose 部署路径不可用：前端 5174→80 端口错配、构建期缺 VITE_API_BASE_URL、nginx.conf 孤儿、8000/8002 分裂、redis/chromadb 无鉴权暴露；start.py 硬编码端口+check_env 运算符优先级误报；stop.bat 容器名不对 | dx | MED | M | LOW | HIGH | `docker-compose.yml:24-35`; `frontend/Dockerfile:19-22`; `nginx.conf:78-79`; `start.py:26,75-98`; `stop.bat` |
| 29 | 文档权威冲突与漂移：README 引用已废弃 ARCHITECTURE.md；RULES 国产栈红线 vs anthropic/openai 在依赖+代码+配置；roadmap 端口/状态过期、把已存在模块标「未实现」 | docs | MED | XS | LOW | HIGH | `RULES.md:8` vs `README.md:225`; `config.py:111-113`; `RESOURCES_AND_ROADMAP.md:149-155` |
| 30 | 仓库卫生：`backend/_err.txt`/`_start.bat`/`sandbox_wrapper.py` 违反 RULES 入库；`_plugins/` 未 ignore；根目录 npm 污染（package.json/package-lock.json/node_modules 遗留）；19 文件未提交 | dx | LOW | XS | LOW | HIGH | `git ls-files backend`; `git status`; 根 `package.json`（仅 @tailwindcss/typography 误装残留） |
| 31 | 5 个 god files：knowledge_routes.py 1325 行 / nodes.py 1226 行 / path_generator.py 1158 行 / retriever.py 677 行 / knowledge/index.vue 814 行；nodes.py 未按原计划拆分 core/agents/ 五文件 | tech-debt | MED | L | MED | HIGH | `backend/app/api/knowledge_routes.py`; `core/nodes.py`; `learning/path_generator.py`; `knowledge/retriever.py`; `frontend/src/pages/knowledge/index.vue` |
| 32 | 逻辑重复：config.py:111-120 与 providers/__init__.py:96-102 各自维护一套 provider→base_url/模型映射（已漂移）；export_routes.py 手写 markdown 剥离器与前端 marked 渲染行为不一致 | tech-debt | LOW | S | LOW | MED | `backend/app/config.py:111-120`; `core/llm/providers/__init__.py:96-102`; `api/export_routes.py` |

## Direction (separate)

- **DIR-1 补全并跑通 docker 全栈部署**：代码已为容器化预留全部开关（`CHROMA_HTTP_URL`、`SANDBOX_BACKEND=docker`、Dockerfile.sandbox），但 compose/nginx 三处断点使 README 承诺不可用。修复成本低（发现 #28），是产品化第一步。
- **DIR-2 把论文质检接入闭环**：`backend/scripts/paper_quality_check.py`（12 项评分）只被手工测试脚本引用，未接入 API/前端；将其接入 `/solution` 完成后自动反馈，完成「练→评」学习闭环。
- **DIR-3 导师模式**：ARCHITECTURE.md:455 明确标注为「建议二期」的延期项（非文档矛盾），学习系统数据模型已按用户隔离（`MasteryTracker` 按 user_id 存储），实现成本被现有架构摊薄——设计/spike 型计划。
- **DIR-4 刷新路线图文档**：RESOURCES_AND_ROADMAP.md 将 working_memory/episodic_memory/checkpoint 标为「❌ 未实现」而代码已存在；成就服务 `achievement_service.py` 已存在但文档仍列在 Phase 4 计划——先校准文档再决定方向。
- **DIR-5 成就服务持久化**：`backend/app/services/achievement_service.py` 已实现但纯内存（load_events 为 pass/TODO），每次重启清零；接入 SQLite 会话存储后即可让 `/progress` 页的成就记录真实可积累——现有架构一步之遥。
- **DIR-6 LaTeX 论文导出**：`api/export_routes.py` 已有 DOCX 导出管线，且 `path_generator.py` 已产出 LaTeX 内容——加一条 LaTeX 导出路由是「相邻可能」，直接服务国赛/美赛提交格式。智能体插话协作（ARCHITECTURE Phase 4）确认未交付，可作后续方向但优先级低于上述项。

## Execution order & status

| Plan | Title | Priority | Effort | Depends on | Status |
|------|-------|----------|--------|------------|--------|
| 001 | 修复路径穿越与文件接口鉴权（发现 1、4） | P1 | XS-S | none | IN PROGRESS（代码完成，待测试验证） |
| 002 | 修复论文导出打印窗口 XSS（发现 2） | P1 | S | none | IN PROGRESS（子代理 C 实施中） |
| 003 | 修复方案模式状态机：回退死循环 + logger NameError + 取消生效（发现 9、10、12） | P1 | S-M | none | IN PROGRESS（子代理 A 实施中） |
| 004 | 建立验证基线：测试 harness + 表征测试 + lint/typecheck + CI（发现 26） | P1 | L | none（先于任何重构） | IN PROGRESS（脚本已加，测试套件待写） |
| 005 | 暴露面收敛：会话/task/files 鉴权 + 绑定 127.0.0.1 + DEBUG=false 校验（发现 4、5） | P2 | S | 001 | IN PROGRESS（代码完成，待测试验证） |
| 006 | 沙箱默认 Docker + 容器加固（发现 3） | P2 | M | none | IN PROGRESS（代码完成，待验证） |
| 007 | 检索性能与融合数学（发现 21、22、24、25） | P2 | M | none | IN PROGRESS（子代理 B 实施中） |
| 008 | SQLite 连接复用（发现 23） | P2 | S | none | DONE（待测试） |
| 009 | 前端批量修复（发现 8、14-20） | P2 | M | none | IN PROGRESS（子代理 C 实施中） |
| 010 | 验证基线补齐：pytest 套件 + CI（发现 26） | P1 | L | 005/007/009 | TODO |
| 011 | 依赖治理 + 部署修复 + 卫生（发现 27、28、30、32、33） | P2 | M | none | IN PROGRESS（卫生/依赖清单完成，部署待改） |
| 012 | 文档权威校准（发现 29） | P2 | S | none | DONE |

## Findings considered and rejected

- API key 明文存 `backend/data/apikeys.json`：RULES.md §5 明示的本地单机设计决策，by-design；其风险已并入发现 1（路径穿越使其可被外部读取）。
- npm audit 34 个高危 advisory 本身：全部位于未使用的 `render-jupyter-notebook-vue` → `@jupyterlab/*` 链，已并入发现 27 的修复理由（删除未用依赖即消除）。
- 安全响应头缺失：`nginx.conf` 已有 nosniff/X-Frame-Options，且 nginx 本身是孤儿配置，并入发现 28。
- Web 搜索结果 prompt-injection 面：通用 LLM 应用风险，已并入发现 3 的影响说明（信任边界=沙箱）。
- `.gitignore` 中文注释乱码：字节级验证为 UTF-8（PowerShell 默认 GBK 解码显示所致），非缺陷。
- 论文导出三路重复（exportPaper.ts / export_routes.py / paper_quality_check.py）：核实为三种不同产物（打印 HTML / DOCX / 评分），非重复实现。
- README「7 智能体 + 55+ 学习单元」：核实为 61 单元 / 62 条 CONTENT_LIBRARY 条目，声明属实。
- SQLite SQL 注入：全部参数化 + 列白名单（`sqlite_session_store.py:161,167`），安全。
- YAML 不安全加载：全部 `safe_load`（`knowledge/loader.py:25`），安全。
- JWT 算法混淆/过期：HS256 固定 + exp 强制（`auth/dependencies.py:36,43`），安全。
