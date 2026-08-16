# MathModelAgent 后端云化镜像（生产部署 · 沙箱 subprocess 模式）
# 与本地 Dockerfile.sandbox 的区别：OCR/PDF/中文字体直接装进主镜像，
# 因为容器内无法再套 Docker 硬隔离，沙箱回退 subprocess 在同一环境执行
FROM python:3.11-slim

WORKDIR /app

# ── 系统依赖：tesseract 中英文 OCR + poppler（PDF 转图）+ Noto CJK（中文图表）──
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-chi-sim \
        tesseract-ocr-chi-tra \
        tesseract-ocr-eng \
        poppler-utils \
        fonts-noto-cjk \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# ── Python 依赖（pip 安装，替代 poetry；poetry-core 构建后端仍被 pip 使用）──
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e . -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn

COPY . .

EXPOSE 8002

# HOST/PORT 由 .env.production 注入（settings.host/port），此处仅兜底
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "1", "--limit-concurrency", "4", "--timeout-keep-alive", "30"]
