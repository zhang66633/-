# 003 沙箱默认 Docker + 隔离加固（发现 #3）

## Status
- **Priority**: P2 · **Effort**: M · **Risk**: MED · **Depends on**: none · **Category**: security
- **Planned at**: commit 1c03e8b, 2026-08-14

## Context
默认 `SANDBOX_BACKEND=subprocess`，其 Windows 下无 rlimit（`preexec_fn` 返回 None）、socket 补丁仅拦 `connect`（`connect_ex`/子进程/ctypes 可绕过），LLM 生成代码（受 prompt-injection 影响）可读 `backend/.env` 全部 key、写入持久化。PLAN_V2 §1.2 已承认「Windows 下才有真正的内存限制」而默认未改。

## Current state
- `backend/app/sandbox/executor.py:29-44` — `_make_preexec_fn` 无 `resource` 模块时返回 None
- `executor.py:235-243` — 仅 patch `_socket.socket.connect`
- `backend/app/config.py:79` — `sandbox_backend: str = "subprocess"`
- `executor.py:161-170` — docker run 仅 `--network=none --memory --memory-swap`

## Spec
1. 默认改 `docker`；`docker` 不存在/镜像缺失时回退 subprocess 并打 WARN 日志（保留本机无 Docker 场景可用性）
2. subprocess 模式补强：patch `socket.socket.connect` **与** `connect_ex`；wrapper 头部用 `os.environ` 二次确认无代理；文档标注「仅限可信输入」
3. docker 命令加固：`--cap-drop=ALL --security-opt no-new-privileges --pids-limit=64 --read-only --tmpfs /tmp` + 非 root 用户（`Dockerfile.sandbox` 加 `USER` 或 run 加 `--user 65534:65534`，输出目录 `:rw` 单独挂载）
4. `README.md` 沙箱段落同步说明默认行为与回退条件

## Verification
- [ ] 有 docker：`docker run --rm --network=none mathmodel-sandbox python -c "import urllib.request; urllib.request.urlopen('http://example.com')"` 失败
- [ ] 无 docker：subprocess 模式跑通且日志含 WARN
- [ ] sandbox 代码尝试 `socket.socket().connect_ex(...)` 被拦
