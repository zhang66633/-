"""API 路由入口 — 注册子路由 + Auth/Health 内联路由。"""
import logging, os
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import RedirectResponse, JSONResponse
import httpx
import jwt

from .chat_routes import chat_router
from .ws import ws_router
from .knowledge_routes import knowledge_router
from .apikeys import apikeys_router
from .tasks import tasks_router
from .files import files_router
from .export_routes import export_router
from .schemas.response import HealthResponse
from ..config import get_settings
from ..services.session import get_session_manager

logger = logging.getLogger(__name__)

api_router = APIRouter()
api_router.include_router(ws_router)
api_router.include_router(knowledge_router)
api_router.include_router(chat_router)
api_router.include_router(apikeys_router)
api_router.include_router(tasks_router)
api_router.include_router(files_router)
api_router.include_router(export_router)

# ── Auth（内联，轻量 OAuth）──

from ..auth import GitHubUser, get_current_user, ALLOWED_CONTRIBUTORS, TokenResponse, UserResponse

_auth_router = APIRouter()

@_auth_router.get("/auth/login")
async def github_login():
    settings = get_settings()
    authorize_url = (
        f"https://github.com/login/oauth/authorize?"
        f"client_id={settings.github_client_id}"
        f"&redirect_uri={settings.github_redirect_uri}"
    )
    return {"authorize_url": authorize_url}

@_auth_router.get("/auth/callback")
async def github_callback(code: str = Query(...)):
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            data={"client_id": settings.github_client_id,
                  "client_secret": settings.github_client_secret, "code": code},
            headers={"Accept": "application/json"},
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="无法获取 GitHub access token")
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(400, detail="GitHub OAuth 失败: " + str(token_data))
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_resp.status_code != 200:
            raise HTTPException(400, detail="无法获取 GitHub 用户信息")
        gh_user = user_resp.json()
    login = gh_user.get("login", "")
    if login.lower() not in {c.lower() for c in ALLOWED_CONTRIBUTORS}:
        raise HTTPException(status_code=403, detail=f"仅项目贡献者可登录，当前: {login}")
    from .auth.dependencies import create_jwt

    token = create_jwt(GitHubUser(
        id=gh_user.get("id", 0),
        login=login,
        name=gh_user.get("name", login),
        avatar_url=gh_user.get("avatar_url", ""),
    ))
    return TokenResponse(
        access_token=token,
        user=GitHubUser(
            id=gh_user.get("id", 0),
            login=login,
            name=gh_user.get("name", login),
            avatar_url=gh_user.get("avatar_url", ""),
        ),
    )

@_auth_router.get("/auth/user")
async def get_user_info(user: GitHubUser | None = Depends(get_current_user)):
    if not user:
        return UserResponse(authenticated=False)
    return UserResponse(
        authenticated=True,
        user=user,
        is_contributor=user.login.lower() in {c.lower() for c in ALLOWED_CONTRIBUTORS},
    )

@_auth_router.post("/auth/logout")
async def logout():
    return {"success": True}

@api_router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok", service="math-model-agent", version="0.1.0")

# 合并 auth 子路由
for route in _auth_router.routes:
    api_router.routes.append(route)
