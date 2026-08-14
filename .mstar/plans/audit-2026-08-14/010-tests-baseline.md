# 010 验证基线：pytest 表征测试 + 前端 lint/typecheck + CI（发现 #26）

## Status
- **Priority**: P1（全部重构的前置） · **Effort**: L · **Risk**: LOW · **Depends on**: none（先行落地，测试目标随各计划同步补） · **Category**: tests
- **Planned at**: commit 1c03e8b, 2026-08-14

## Context
前后端零自动化测试、零 CI、biome.json 未接线、无 lint/typecheck 脚本。最高频变更文件（router.py 23 次、tasks.py 21 次、chat_routes.py 17 次、nodes.py 15 次）全部无测试。

## Current state
- `backend/pyproject.toml:46-51` — pytest/pytest-asyncio 声明未用；无 tests/ 目录
- `frontend/package.json:6-10` — 仅 dev/build/preview；`biome.json` 存在未接线
- 无 `.github/workflows`、无 AGENTS.md/CLAUDE.md

## Spec
1. `backend/tests/` + `backend/pytest.ini`（asyncio_mode=auto）：首套表征测试锁定修复行为——`test_files_path_guard.py`（#1）、`test_router.py`（#9 回退序列）、`test_mastery_tracker.py`（#11 幂等）、`test_sqlite_store.py`（#4 用户隔离 + #23 连接复用）、`test_retriever_fusion.py`（#24 数学）、`test_apikeys_ssrf.py`（#7）、`test_oauth_state.py`（#6）
2. `frontend/package.json` 加 `typecheck: vue-tsc --noEmit`（tsconfig tsBuildInfoFile 指向 node_modules/.cache 防产物）、`lint: biome check src`、`format: biome format --write src`
3. `.github/workflows/ci.yml`：backend `pip install -e .[dev]` + pytest；frontend `pnpm install --frozen-lockfile` + typecheck + lint
4. 根 `AGENTS.md`：技术栈、启动/测试/提交命令、红线摘要（供后续 agent 会话使用）

## Verification
- [ ] `cd backend && pytest -q` 全绿
- [ ] `cd frontend && pnpm exec vue-tsc --noEmit && pnpm exec biome check src` 零错误
- [ ] 无网络 CI 等价验证：本地跑通同组命令
