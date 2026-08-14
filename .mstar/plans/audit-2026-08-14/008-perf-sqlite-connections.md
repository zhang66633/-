# 008 SQLite 会话存储连接管理（发现 #23）

## Status
- **Priority**: P2 · **Effort**: S · **Risk**: LOW · **Depends on**: none · **Category**: perf
- **Planned at**: commit 1c03e8b, 2026-08-14

## Context
每个方法调用 `sqlite3.connect()` 新建连接，`with conn` 的 `__exit__` 只 commit 不 close（句柄靠 GC），且每连接重放 `PRAGMA journal_mode=WAL`。

## Current state
- `backend/app/services/sqlite_session_store.py:81-87` — `_get_conn()` 每次新建 + PRAGMA 重放；约 15 处 `with self._get_conn() as conn:`

## Spec
1. 初始化时执行一次 `PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON`（`_init_db` 内）
2. `threading.local` 存放每线程单连接（`check_same_thread=False`），方法内复用；写操作显式 `conn.commit()`，读无需
3. 保留现有 `self._lock`（写串行化）与参数化 SQL 不变；提供 `close()` 供 shutdown 调用（main.py lifespan 可选接入）

## Verification
- [ ] 单测：连续 100 次读写后连接对象复用（id 一致）；并发读写无 `sqlite3.ProgrammingError`
- [ ] 手工：消息同步接口正常、无句柄泄漏（任务管理器观察）
