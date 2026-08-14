"""Auth module — GitHub OAuth login + JWT session management."""

from .dependencies import (
    create_jwt,
    decode_jwt,
    get_current_user,
    require_auth,
    require_contributor,
)
from .github import ALLOWED_CONTRIBUTORS
from .schemas import GitHubUser, TokenResponse, UserResponse

__all__ = [
    "GitHubUser",
    "TokenResponse",
    "UserResponse",
    "ALLOWED_CONTRIBUTORS",
    "create_jwt",
    "decode_jwt",
    "get_current_user",
    "require_auth",
    "require_contributor",
]
