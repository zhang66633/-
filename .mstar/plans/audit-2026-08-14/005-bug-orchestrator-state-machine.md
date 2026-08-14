# 005 编排器状态机三 bug + 工作记忆异步重写（发现 #9、#10、#12、#13）

## Status
- **Priority**: P1 · **Effort**: M · **Risk**: MED · **Depends on**: 010（表征测试先行/同步落地） · **Category**: bug
- **Planned at**: commit 1c03e8b, 2026-08-14

## Context
验证 FAIL 回退进入 modeling 死循环（烧 ~50 次建模 LLM 调用后 recursion_limit 报错）；导出节点 except 内 `logger` 未定义 → NameError；任务取消事件管线内从不检查；工作记忆异步重写在无事件循环线程静默失败（solution-via-chat 路径 problem_doc 永不更新）。

## Current state
- `backend/app/core/nodes.py:896-901` — FAIL 置 `verification_passed=False` + `rollback_target="modeling"` + `retry_count+1`
- `backend/app/core/router.py:39-52` — `verification_passed` 假且 `rollback_target` 存在即无条件回 `modeling_agent`
- `backend/app/core/nodes.py:466-532` — `modeling_agent_node` 不重置标志、不消费 retry_count
- `nodes.py:1293` — `logger.warning(...)`，全模块无 `logger = logging.getLogger(__name__)`
- `nodes.py:66-73` — `_is_cancelled` 定义后无调用；`api/tasks.py:287-322` astream 循环不检查
- `nodes.py:87-90` — `asyncio.get_event_loop()` 在无 loop 线程抛 RuntimeError 被 `except: pass` 吞掉

## Spec
1. 回退语义修正：`after_agent_router` 仅在 `rollback_target` 且本次为该目标的**首次回退**时路由一次（进入回退分支时把 `retry_count` 减一 + 置 `verification_passed=None` 类「待验证」态），重跑 modeling→solving 后验证节点自然再进入；或等价地引入显式 `rollback_pending` 标志由 modeling 节点消费。保持 plan 顺序不动
2. `nodes.py` 顶部加 `logger = logging.getLogger(__name__)`
3. 取消：`_run_orchestrator` 的 astream 循环每步检查 `_is_cancelled(task_id)` → 置 status cancelled 并 break；各节点入口调用一次（工具循环内可选）
4. 工作记忆：`_save_working_memory` 改为「若当前线程无运行 loop 则跳过异步重写并 WARN，有则 `loop.run_in_executor`」；`_run_orchestrator_sync` 已建 loop 的路径保持原行为；删除裸 `except: pass` 改为 `except Exception: logger.warning(...)`

## Verification
- [ ] 单元测试：构造 FAIL 状态 → 断言路由序列 modeling→solving→verification 且 retry_count 递减、最终终态（tests/test_router.py）
- [ ] 取消测试：cancel 后 astream 提前退出、状态为 cancelled
- [ ] `python -c "import app.core.nodes"` 无 ImportError；导出节点异常路径不抛 NameError（测试桩 ResultPackager 抛异常）
