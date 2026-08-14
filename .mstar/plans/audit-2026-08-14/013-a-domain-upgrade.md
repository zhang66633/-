# 013 A 域升级 — 沙箱执行模式 + 工具调用协议 + 架构修正

## Status
- **Priority**: P1 · **Effort**: M · **Risk**: MED · **Depends on**: none · **Category**: direction/tech-debt
- **Planned at**: commit 47a0d40, 2026-08-14 · **Owner**: 开发者 A（建模管线）

## Context
用户三个重点：①docker 跑代码是否必要；②现有工具调用和面板是否先进；③现有架构是否合理。

证据（2026-08-14 实测）：
- 本机 docker CLI 29.4.3 已装，但 **Docker Desktop 守护进程未运行**（npipe 连不上）。当前 `executor.run()` 仅当 `which("docker") is None` 才回退 subprocess——daemon 未启动时 `docker run` 直接失败，所有 run_code 全挂。**docker 非必须，必须做成自动回退**。
- `chat_routes._event_stream` 工具执行是串行 for 循环，无每工具超时（web_search 可挂死），事件协议有 delta/tool_call/tool_result/clarify/code_exec/thinking 但无 duration/ok/error 语义。
- `nodes.py` 验证节点用正则 `\{[^{}]*"verdict"...\}` 抽 JSON（嵌套即失败）；分类/规划节点同样正则抽 JSON；管线无 token 用量观测（writing 393K max_tokens 无成本可见性）。

## Spec（本次一口气做完）

### 1. 沙箱执行模式（重点①）
1. `executor.run()`：docker 分支前先探测 daemon（`docker info --format {{.ServerVersion}}`，timeout 3s）；二进制缺失 **或 daemon 不通** → 回退 subprocess 并 WARN（每次 run 探测太贵 → 进程内缓存探测结果，失败后 60s 内不再探测）
2. 新增 `GET /api/sandbox/status` → `{"backend": "subprocess"|"docker", "available": bool, "reason": str}`（给 B 的面板展示当前沙箱模式）
3. `config.py` 保持 `sandbox_backend: "docker"`（偏好），语义改为「优先 docker，不可用自动回退」；`.env.example`/`AGENTS.md`/README 沙箱段落同步说明 docker 非必须
4. subprocess 模式仍带 socket 补丁 + 告警日志（已有）

### 2. 聊天工具调用协议升级（重点②，为 B 的先进面板提供契约）
1. 并行执行：`_event_stream` 中 tool_calls 分组——KB 检索/数学/搜索等无副作用工具 `asyncio.gather` 并发；`run_code` 串行（`is_concurrency_safe=False` 已有标记，按标记分组）；`ask_user` 保持特殊路径
2. 每工具超时：`asyncio.wait_for(asyncio.to_thread(tool.invoke, args), timeout)`；默认 60s，web_search 30s；超时返回结构化错误
3. 事件协议 v2（向后兼容）：
   - `tool_call` 增 `id`（复用 tc id）与 `status:"running"` 语义不变
   - `tool_result` 增 `ok: bool`、`duration_ms: int`、`error?: str`
   - 并行组开始发 `tool_batch` 事件 `{"names":[...]}`（可选，B 面板可忽略）
4. `NEXT_DEV_PLAN.md` 接口契约小节追加 tool_result v2 结构（B 照此做面板）

### 3. 架构修正（重点③）
1. `nodes.py` 验证节点：正则 JSON 判定替换为 `_extract_json`（node_helpers 已有，兼容 ```json 围栏/裸 JSON/嵌套），`verdict` 与 `rollback_target` 读取逻辑不变
2. 分类/规划节点若有同类正则抽 JSON → 同样换 `_extract_json`（grep 确认后逐处替换）
3. 管线用量观测：`nodes.py` 各节点 `llm.invoke` 后读 `response.usage_metadata`（input/output tokens）→ logger.info 一条（task_id, node, tokens）；`tasks.py` 结束处汇总输出（无需改协议）
4. 不动的：会话两套存储（services/ 归 B，仅记录到 backlog）；写作 393K tokens 预算保留（用户决策过）

## Verification
- [x] AST 全量 + 14 测试套件全过（含新增 test_sandbox_status 5 用例 + test_nodes 扩展嵌套 JSON 2 用例）
- [x] `GET /api/sandbox/status` TestClient 冒烟 200（本机 daemon 未启动 → 正确返回 backend=subprocess）
- [x] run_code 本机真实回退 subprocess 并成功执行 `print(1+1)`（test_run_falls_back_to_subprocess_when_daemon_down）
- [x] 验证节点嵌套 JSON（围栏 + FAIL + rollback_target=solving）测试通过
- [ ] 聊天工具并行真实 LLM 联调（需 API key，真机验证项）

## Implementation notes (2026-08-14)
- 重点①：docker 非必须——`docker_daemon_up()` 探测（60s 缓存）+ daemon 未启动自动回退 subprocess；`/api/sandbox/status` 暴露模式给 B 面板。本机实测 daemon 未开 → 回退路径真实跑通。
- 重点②：chat 工具全部并行执行（asyncio.gather）+ 每工具超时（web_search 30s/其余 60s）+ 事件协议 v2（tool_call.id、tool_result.ok/duration_ms/error、code_exec.ok/duration_ms），契约已写入 NEXT_DEV_PLAN §4.4。
- 重点③：验证节点判定改 `_extract_verdict_json`（平衡花括号+围栏+散文容忍）；全管线 16 个 LLM 调用点接 `_log_usage` token 用量观测（writing 各章节单独计）。
- 跨域小修：B 的 test_achievement_service.py 脚本运行器加 `ignore_cleanup_errors=True`（Windows sqlite 连接未关致临时目录删除 WinError 32）；深层修复 LearningStore/PracticeStore 提供 close() 属 B 域，已留言。
