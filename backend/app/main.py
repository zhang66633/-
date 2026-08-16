"""FastAPI application entry point."""

import traceback
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

# 显式加载 .env（确保任何启动方式都能读到）
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(_env_path)

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.router import api_router
from .config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown events."""
    import asyncio

    settings = get_settings()

    # JWT secret 安全校验
    if settings.jwt_secret == "set-in-env-file":
        if not settings.debug:
            raise RuntimeError("jwt_secret 未配置！生产环境必须在 .env 中设置 JWT_SECRET。")
        import secrets as _secrets

        settings.jwt_secret = _secrets.token_urlsafe(32)
        print(
            "[WARNING] JWT_SECRET 未配置，已生成随机临时密钥（重启后 token 失效）。"
            "请在 .env 中设置 JWT_SECRET。",
            flush=True,
        )

    # 知识库向量索引：不存在则自动重建（后台线程，不阻塞启动）
    _needs_rebuild = False
    if settings.chroma_http_url:
        # 远程模式：通过 HTTP 检查 collection 是否存在
        print(f"[INFO] ChromaDB 远程模式: {settings.chroma_http_url}", flush=True)
        try:
            from urllib.parse import urlparse

            import chromadb

            parsed = urlparse(settings.chroma_http_url)
            client = chromadb.HttpClient(
                host=parsed.hostname or "localhost", port=parsed.port or 8000
            )
            collections = client.list_collections()
            names = [c if isinstance(c, str) else c.name for c in collections]
            if "kb_docs" not in names:
                _needs_rebuild = True
        except Exception as e:
            print(f"[WARNING] 无法连接远程 ChromaDB ({e})，跳过自动重建检查", flush=True)
    else:
        chroma_db_file = Path(settings.chroma_dir) / "chroma.sqlite3"
        if not chroma_db_file.exists():
            _needs_rebuild = True

    if _needs_rebuild:
        print("[INFO] 向量索引不存在，后台自动重建...", flush=True)

        def _rebuild_index():
            try:
                from .knowledge.embedder import KBEmbedder

                embedder = KBEmbedder(
                    kb_root=settings.kb_root,
                    persist_dir=settings.chroma_dir,
                )
                count = embedder.build_index()
                print(f"[INFO] 向量索引自动重建完成，共 {count} 篇文档", flush=True)
            except Exception as e:
                print(f"[WARNING] 向量索引自动重建失败: {e}", flush=True)

        asyncio.get_event_loop().run_in_executor(None, _rebuild_index)
    else:
        print("[INFO] 向量索引已存在，跳过重建", flush=True)

    print(f"MathModelAgent backend starting on {settings.host}:{settings.port}")

    yield

    # Clean up Redis publisher
    from .services.redis_pubsub import shutdown_publisher

    shutdown_publisher()
    print("MathModelAgent backend shutting down.")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    get_settings()

    app = FastAPI(
        title="Math Model Agent",
        description="数学建模多智能体辅助系统",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS — allow frontend dev server
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 全局异常处理器：500 错误返回 JSON，debug 模式含 traceback 便于排查
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        tb = traceback.format_exc()
        print(f"[UNHANDLED] {request.method} {request.url.path}\n{tb}", flush=True)
        if get_settings().debug:
            return JSONResponse(
                status_code=500,
                content={
                    "detail": f"{type(exc).__name__}: {str(exc)[:300]}",
                    "type": type(exc).__name__,
                    "path": str(request.url.path),
                },
            )
        return JSONResponse(
            status_code=500,
            content={"detail": "服务器内部错误，请稍后重试"},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors(), "type": "RequestValidationError"},
        )

    app.include_router(api_router, prefix="/api")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    # 对齐 RULES.md：uvicorn 不带 --reload（不稳定）
    # limit_concurrency 只放开到 64: 前端一页会并发打 6+ 个请求(健康检查/会话同步/题库),
    # 加上 SSE 流与 WebSocket 常驻连接,限制 4 会直接 503 拒绝新连接(表现为刷新后题目/聊天记录消失)
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        workers=1,
        limit_concurrency=64,
        timeout_keep_alive=30,
    )
