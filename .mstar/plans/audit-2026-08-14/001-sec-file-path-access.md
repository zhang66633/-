# 001 路径穿越修复 + 文件/会话接口访问控制（发现 #1、#4）

## Status
- **Priority**: P1 · **Effort**: S · **Risk**: LOW · **Depends on**: none · **Category**: security
- **Planned at**: commit 1c03e8b, 2026-08-14

## Context
`/api/task_files/{task_id}/{filename}` 的路径守卫允许 `..`，配合 resolve 后 `startswith` 校验可上跳目录，匿名读取 `backend/data/apikeys.json`（明文 LLM key）与 `sessions.json`（838KB 聊天记录）。文件下载与任务文件接口无鉴权。

## Current state
- `backend/app/api/files.py:15` — `_SAFE_NAME_RE = ^[a-zA-Z0-9._-]+$` 匹配 `..`
- `backend/app/api/files.py:114-127` — `get_task_file` 以 `(root/data/task_files/task_id).resolve()` 为基，`task_id=".."` 时基目录变 `data/`，`startswith` 校验失效
- `files.py:42,83,99,114` — 上传/下载/图片/任务文件全部无 `Depends`
- `session_routes.py:52-152` — 会话 CRUD 全部无鉴权、无属主
- 实测 `backend/data/apikeys.json`(1086B)、`sessions.json`(838478B) 存在

## Spec
1. `_validate_path_segment`：拒绝值为 `.`/`..` 或仅由点组成的段；正则不变
2. `get_task_file`/`get_image`：`file_dir.resolve()` 后用 `file_path.is_relative_to(file_dir)` 做 containment 校验（Python≥3.9）
3. 路由鉴权（保留 guest 模式）：`get_current_user` 可选注入；会话接口按 `user.login`（未登录="guest"）隔离——`sqlite_session_store` 增 `user_id TEXT DEFAULT 'guest'` 列 + 索引，list/get/update/delete/messages 方法加 `user_id` 过滤；存量行迁移为 guest
4. `download_file` 保留匿名（file_id 为 32-bit 随机，绑定 localhost 后风险可接受），但 `task_files` 读取与图片服务加属主校验

## Tasks
- [ ] files.py 路径守卫 + containment + `is_relative_to`
- [ ] sqlite_session_store.py 建表语句加 user_id 列（含迁移：ALTER TABLE 若缺列）+ 各方法 user_id 参数与过滤
- [ ] session_routes.py 注入 `get_current_user` → uid（guest 回退）
- [ ] tasks.py 的任务文件区读取沿用同一校验（确认无第二处拼接路径）

## Verification
- [ ] `python -c` 导入检查：`from app.api.files import _validate_path_segment; assert _validate_path_segment("..")` 抛 400（pytest 用例落地后转入 tests/）
- [ ] 手工 curl（--path-as-is）：`/api/task_files/../apikeys.json` → 400
- [ ] 会话隔离：guest 与登录用户看不到彼此会话
