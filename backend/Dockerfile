# MathModelAgent 后端 — 云服务器生产镜像
#
# 关键云化点：
# - subprocess 沙箱（容器内无法嵌套 Docker；Unix rlimits 在容器内生效）
# - 系统依赖含 tesseract 中英文 + poppler + 中文字体（沙箱 OCR/图表中文渲染）
# - HOST=0.0.0.0 对外监听（经反向代理/隧道暴露，不要直接裸奔公网）
FROM python:3.11-slim

# ── 系统依赖：OCR + 中文字体（沙箱 subprocess 模式需要）──
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-chi-sim \
        tesseract-ocr-eng \
        poppler-utils \
        fonts-noto-cjk \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先装依赖（利用 Docker 层缓存），再拷代码
COPY pyproject.toml ./
COPY app ./app
COPY sandbox_wrapper.py ./

RUN pip install --no-cache-dir .

# 云化默认值（可被 docker-compose / 环境变量覆盖）
ENV HOST=0.0.0.0 \
    PORT=8002 \
    DEBUG=false \
    SANDBOX_BACKEND=subprocess \
    SANDBOX_MAX_MEMORY_MB=1024 \
    PYTHONIOENCODING=utf-8

EXPOSE 8002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "1", "--timeout-keep-alive", "30"]
