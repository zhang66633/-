"""Auth dependencies — FastAPI Depends() callables for route protection."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import get_settings
from .github import GitHubUser, ALLOWED_CONTRIBUTORS

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)

JWT_EXPIRE_DAYS = 7


# ── JWT helpers ─────────────────────────────────────────────────────


def create_jwt(user: GitHubUser) -> str:
    """Create a signed JWT for the authenticated user (7-day expiry)."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "login": user.login,
        "name": user.name,
        "avatar_url": user.avatar_url,
        "iat": now,
        "exp": now + timedelta(days=JWT_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_jwt(token: str) -> GitHubUser | None:
    """Decode and validate a JWT, returning the GitHubUser."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        # 兼容旧 token：sub 可能是 string(login) 或 int(id)
        sub_raw = payload.get("sub", 0)
        try:
            uid = int(sub_raw)
        except (ValueError, TypeError):
            uid = 0
        return GitHubUser(
            id=uid,
            login=payload.get("login", ""),
            name=payload.get("name"),
            avatar_url=payload.get("avatar_url"),
        )
    except jwt.InvalidTokenError:
        return None


# ── FastAPI dependencies ────────────────────────────────────────────


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> GitHubUser | None:
    """Extract the current user from the Authorization header.

    Returns None if no valid token is present (does NOT raise 401).
    """
    if credentials is None:
        return None
    user = decode_jwt(credentials.credentials)
    if user is not None:
        request.state.user = user
    return user


async def require_auth(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> GitHubUser:
    """Require a valid JWT token.  Raises 401 if missing or invalid."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="请先登录")
    user = decode_jwt(credentials.credentials)
    if user is None:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    request.state.user = user
    return user


async def require_contributor(
    user: GitHubUser = Depends(require_auth),
) -> GitHubUser:
    """Require the authenticated user to be a repository contributor.

    Only zhang66633 and shu639 are allowed to manage the knowledge base.
    Raises 403 if the user is not a contributor.
    """
    if user.login.lower() not in {c.lower() for c in ALLOWED_CONTRIBUTORS}:
        raise HTTPException(
            status_code=403,
            detail=f"当前登录: {user.login} — 不在贡献者列表中。请联系 zhang66633 添加你的 GitHub 用户名到 ALLOWED_CONTRIBUTORS",
        )
    return user
