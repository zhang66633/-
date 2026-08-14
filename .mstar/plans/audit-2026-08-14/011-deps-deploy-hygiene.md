# 011 依赖治理 + 部署修复 + 仓库卫生（发现 #27、#28、#30、#32、#33）

## Status
- **Priority**: P2 · **Effort**: M · **Risk**: LOW · **Depends on**: none · **Category**: deps/dx
- **Planned at**: commit 1c03e8b, 2026-08-14

## Context
依赖无锁文件、全开放下限、alpha 依赖、pnpm/package-lock 双锁；npm audit 34 高危（全部经未使用的 render-jupyter-notebook-vue → @jupyterlab 链）；docker-compose 部署路径三处断点；根目录 npm 误装残留；4 个被代码引用的文件未入库（fresh clone 直接坏）；provider 映射重复维护；RULES 禁止入库的运行产物仍在 git。

## Current state
- `backend/pyproject.toml:8-44` 全 `>=`；无 `poetry.lock`；build-backend=poetry-core vs README `pip install -e .`
- `frontend/package.json:11-30` — `md-editor-v3`/`render-jupyter-notebook-vue`/`motion-v@1.0.0-alpha.0`/`@inspira-ui/plugins@0.0.1`/`theme-colors` 零 import（grep 证实）
- `docker-compose.yml:24-35` — frontend `5174:5174` vs 容器 nginx 80；构建期无 VITE_API_BASE_URL；无 nginx 服务
- `nginx.conf:78-79` — `/health` → `backend/health/ready`（不存在，实际 `/api/health`）
- 根 `package.json`（仅 @tailwindcss/typography）、`package-lock.json`、`node_modules/` 误装残留；`_plugins/` 未 ignore
- `backend/_err.txt`、`backend/_start.bat`、`backend/sandbox_wrapper.py` 在 git
- 未入库但被引用：`backend/app/core/prompts/preprocessing.py`、`backend/app/services/result_packager.py`、`frontend/src/components/paper/`（4 文件）、`frontend/src/assets/paper.css`（`nodes.py:50,1266`、`tasks.py:606`、`BubbleAgent.vue:8`、`solution/index.vue:135` 引用）
- `config.py:111-120` vs `core/llm/providers/__init__.py:96-102` — provider→base_url/模型映射两处维护

## Spec
1. 依赖：`pnpm remove` 5 个未用依赖（`motion-v`、`@inspira-ui/plugins`、`theme-colors`、`md-editor-v3`、`render-jupyter-notebook-vue`），删除根 `package-lock.json`（统一 pnpm-lock.yaml），若可运行 `poetry lock` 生成 `backend/poetry.lock` 否则在 pyproject 关键直接依赖加保守上限并注释
2. 部署：compose 前端改 `"80:80"` + build args（`VITE_API_BASE_URL`/`VITE_WS_URL` 注入），新增 nginx 服务挂载 `nginx.conf`（修正 `/health` 与 ws 路径、限流保留）；redis/chromadb 去掉 host 端口发布（仅内网服务，需要时显式开）
3. 卫生：`.gitignore` 加 `_plugins/`、根 `node_modules/`、`package.json`/`package-lock.json`（根，保留 frontend/ 内）；`git rm --cached` 三个运行产物；`git add` 4 组被引用的未入库文件（#33）
4. provider 映射收敛到 `providers/__init__.py` 单一真源，`config.get_llm_config` 引用之（#32）

## Verification
- [ ] `git status` 干净（除 .mstar/、_plugins/ 被忽略）
- [ ] fresh-clone 模拟：`git ls-files | grep -E "preprocessing|result_packager|components/paper|paper.css"` 全部命中
- [ ] `pnpm install --frozen-lockfile && pnpm build` 成功；`pnpm audit --prod` 高危归零
- [ ] `docker compose config` 通过（有 docker 时）；端口/路径一致

## Implementation notes (2026-08-14)

- 前端依赖清单已重写（删 5 个未用依赖、`@tailwindcss/typography` 由根目录迁入 frontend 依赖、加 typecheck/lint/format 脚本）；pnpm-lock.yaml 经 `pnpm install` 同步，根 `package-lock.json` 与根 `package.json` 删除、根 `node_modules/` 忽略。
- 部署已修：compose 端口 5174:80 + build args 注入 VITE_API_BASE_URL/WS_URL；backend 127.0.0.1:8002:8000；redis/chromadb 仅 127.0.0.1 发布；nginx.conf `/health` 指向修复；start.py check_env 重写（正则 + 占位符检测）；stop.bat 改 `docker compose down`。
- `poetry.lock` 未生成：本机无 poetry（Python 3.14 环境）。CI 用 `pip install -e .` 解析；建议后续在装有 poetry 的环境补 `poetry lock` 后入库。
- `sandbox_wrapper.py` 保留入库：`Dockerfile.sandbox` 构建上下文依赖它（非一次性脚本，属沙箱镜像构建产物）。

