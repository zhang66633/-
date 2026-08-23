#!/usr/bin/env bash
# Math Model Agent — 一键安装 (Linux / macOS)
set -e
cd "$(dirname "$0")"

echo "=============================================="
echo " Math Model Agent — 一键安装"
echo "=============================================="

# ── 1. 环境检查 ────────────────────────────────
if ! command -v python3 >/dev/null 2>&1; then
  echo "[错误] 未找到 python3。请安装 Python 3.11+ 后重试。"
  exit 1
fi
echo "[1/5] Python: $(python3 --version 2>&1)"

if ! command -v pnpm >/dev/null 2>&1; then
  echo "[错误] 未找到 pnpm。请先执行: npm i -g pnpm  或  corepack enable"
  exit 1
fi
echo "[1/5] pnpm 已就绪"

# ── 2. 后端: 虚拟环境 + 依赖 ───────────────────
echo "[2/5] 创建后端虚拟环境 .venv ..."
if [ ! -x ".venv/bin/python" ]; then
  python3 -m venv .venv
fi

echo "[3/5] 安装后端依赖(首次约 3-8 分钟)..."
.venv/bin/python -m pip install --upgrade pip >/dev/null 2>&1 || true
.venv/bin/python -m pip install -e backend

# ── 3. 生成 .env ───────────────────────────────
if [ ! -f "backend/.env" ]; then
  echo "[4/5] 生成 backend/.env(含随机 JWT_SECRET)..."
  cp backend/.env.example backend/.env
  SECRET=$(.venv/bin/python -c "import secrets;print(secrets.token_hex(32))")
  .venv/bin/python -c "import io;p='backend/.env';s=io.open(p,encoding='utf-8').read().replace('JWT_SECRET=change-me-to-a-random-string','JWT_SECRET=$SECRET').replace('PORT=8000','PORT=8002').replace('SANDBOX_BACKEND=docker','SANDBOX_BACKEND=subprocess');io.open(p,'w',encoding='utf-8').write(s)"
else
  echo "[4/5] backend/.env 已存在,跳过"
fi

# ── 4. 前端依赖 ────────────────────────────────
echo "[5/5] 安装前端依赖 pnpm install(首次约 2-5 分钟)..."
(cd frontend && pnpm install)

# ── 5. 可选: Docker 沙箱镜像 ───────────────────
if [ "${1:-}" = "--docker" ]; then
  echo "[可选] 构建沙箱镜像 mathmodel-sandbox ..."
  if docker build -t mathmodel-sandbox -f backend/Dockerfile.sandbox backend; then
    .venv/bin/python -c "import io;p='backend/.env';s=io.open(p,encoding='utf-8').read().replace('SANDBOX_BACKEND=subprocess','SANDBOX_BACKEND=docker');io.open(p,'w',encoding='utf-8').write(s)"
    echo "[可选] 已启用 docker 硬隔离沙箱"
  else
    echo "[警告] 沙箱镜像构建失败,继续使用 subprocess 模式(功能不受影响)"
  fi
fi

echo
echo "=============================================="
echo " 安装完成!"
echo
echo " 启动:  python3 start.py      (同时启动前后端)"
echo " 前端:  http://localhost:5174"
echo " 后端:  http://127.0.0.1:8002/docs"
echo
echo " 配置 API Key: 打开首页,在「API Key」输入框粘贴你的"
echo " DeepSeek/OpenAI 兼容 Key 即可(仅保存在本机 backend/data)。"
echo " 也可以编辑 backend/.env 填 OPENAI_API_KEY。"
echo "=============================================="
