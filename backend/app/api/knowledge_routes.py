"""知识库路由聚合 — 检索/上传 + CRUD 两个子路由组合（god-files 拆分 #31）。

具体实现见 knowledge_search_routes.py 与 knowledge_crud_routes.py。
"""

from fastapi import APIRouter

from .knowledge_crud_routes import knowledge_router as crud_router
from .knowledge_search_routes import knowledge_router as search_router

knowledge_router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])
knowledge_router.include_router(search_router)
knowledge_router.include_router(crud_router)
