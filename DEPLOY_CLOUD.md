# 云服务器部署指南（后端）

架构：**前端 Cloudflare Pages（已部署）+ 后端云服务器 Docker**。

## 前置条件

- 一台 Linux 云服务器（2C4G 起步，Ubuntu 22.04/24.04 或 Debian 12）
- 已安装 Docker + Docker Compose（`docker compose version` 可执行）

## 部署步骤（服务器上执行）

```bash
# 1. 克隆仓库
git clone https://github.com/zhang66633/NB_project.git
cd NB_project

# 2. 配置密钥
cp backend/.env.production.example backend/.env.production
vi backend/.env.production   # 填 DEEPSEEK key / GitHub OAuth / JWT 随机串

# 3. 构建并启动
docker compose -f docker-compose.cloud.yml up -d --build

# 4. 验证
curl http://localhost:8002/api/health
docker compose -f docker-compose.cloud.yml logs -f backend
```

## 前端指向后端

前端（Cloudflare Pages）构建时需要把 API 指向这台服务器：

1. 前端目录创建 `frontend/.env.production.local`（已 gitignore）：

```bash
VITE_API_BASE_URL=https://你的服务器域名或IP:8002/api
VITE_WS_URL=wss://你的服务器域名或IP:8002/api/ws
```

> WS 需要 HTTPS（wss）——服务器前端最好配 Nginx/Caddy 反代 + TLS 证书，或走 Cloudflare 代理域名。

2. 本地重新构建并部署：

```bash
cd frontend
pnpm build
wrangler pages deploy dist --project-name=math-model-agent --commit-dirty=true
```

## 云化要点（已在镜像/配置内置）

| 项 | 值 | 原因 |
|---|---|---|
| 沙箱 | `SANDBOX_BACKEND=subprocess` | 容器内无法嵌套 Docker；Unix rlimits 生效 |
| 内存上限 | 1024MB（沙箱） | 服务器按需调整 |
| 向量库 | 嵌入式 ChromaDB | 无需独立 chroma 容器 |
| Redis | fakeredis 内存兜底 | 单实例够用 |
| 持久化 | `data/` + `knowledge_base/` 挂卷 | 重启/重建不丢 |
| OCR/中文 | 镜像内置 tesseract 中英文 + Noto CJK | 沙箱图表中文、扫描件 OCR |

## 安全提醒

- 8002 不要直接裸奔公网：用 Nginx/Caddy 反代 + TLS，或 Cloudflare Tunnel；
- GitHub OAuth 回调地址必须与 GitHub App 配置一致（公网域名）；
- `.env.production` 已在 .gitignore，密钥不要提交。
