"""API 路由入口 — 注册子路由 + Auth/Health 内联路由。"""
import logging
import secrets
from fastapi import APIRouter, HTTPException, Query, Depends, Request, Response
from fastapi.responses import JSONResponse
import httpx

from .chat_routes import chat_router
from .ws import ws_router
from .knowledge_routes import knowledge_router
from .apikeys import apikeys_router
from .tasks import tasks_router
from .files import files_router
from .export_routes import export_router
from .knowledge_import_routes import import_router
from .learning_routes import learning_router
from .profile_routes import profile_router
from .session_routes import session_router
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
api_router.include_router(import_router)
api_router.include_router(learning_router)
api_router.include_router(profile_router)
api_router.include_router(session_router)

# ── Auth（内联，轻量 OAuth）──

from ..auth import GitHubUser, get_current_user, ALLOWED_CONTRIBUTORS, TokenResponse, UserResponse

_auth_router = APIRouter()

# OAuth state 防 CSRF：登录时下发随机 state cookie，回调时校验后清除
OAUTH_STATE_COOKIE = "mma_oauth_state"


@_auth_router.get("/auth/login")
async def github_login(response: Response):
    settings = get_settings()
    state = secrets.token_urlsafe(16)
    response.set_cookie(
        OAUTH_STATE_COOKIE, state,
        max_age=600, httponly=True, samesite="lax",
    )
    authorize_url = (
        f"https://github.com/login/oauth/authorize?"
        f"client_id={settings.github_client_id}"
        f"&redirect_uri={settings.github_redirect_uri}"
        f"&state={state}"
    )
    return {"authorize_url": authorize_url}

@_auth_router.get("/auth/callback")
async def github_callback(
    code: str = Query(...),
    state: str = Query(default=""),
    request: Request = None,
    response: Response = None,
):
    # 防 login CSRF：state 必须与登录时下发的 cookie 一致
    cookie_state = request.cookies.get(OAUTH_STATE_COOKIE, "")
    if not cookie_state or not state or not secrets.compare_digest(cookie_state, state):
        raise HTTPException(status_code=400, detail="OAuth state 校验失败，请重新登录")
    response.delete_cookie(OAUTH_STATE_COOKIE)

    settings = get_settings()
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            data={"client_id": settings.github_client_id,
                  "client_secret": settings.github_client_secret,
                  "code": code,
                  "redirect_uri": settings.github_redirect_uri},
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
    from ..auth.dependencies import create_jwt

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


@api_router.get("/sandbox/status")
async def sandbox_status():
    """沙箱执行模式状态（供前端面板展示当前是 Docker 硬隔离还是 subprocess 回退）。"""
    from ..sandbox.executor import docker_daemon_up
    from ..config import get_settings

    settings = get_settings()
    docker_up = docker_daemon_up()
    backend = "docker" if (settings.sandbox_backend == "docker" and docker_up) else "subprocess"
    return {
        "backend": backend,
        "configured": settings.sandbox_backend,
        "docker_available": docker_up,
        "note": ("docker 硬隔离" if backend == "docker"
                 else "docker 不可用（未安装或未启动），已回退 subprocess 模式"),
    }

# 合并 auth 子路由
for route in _auth_router.routes:
    api_router.routes.append(route)
