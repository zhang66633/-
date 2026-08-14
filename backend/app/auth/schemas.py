"""Auth schemas — Pydantic models for authentication."""

from pydantic import BaseModel


class GitHubUser(BaseModel):
    """GitHub user profile returned by OAuth."""

    id: int
    login: str
    name: str | None = None
    email: str | None = None
    avatar_url: str | None = None


class TokenResponse(BaseModel):
    """JWT token returned to the frontend after login."""

    access_token: str
    token_type: str = "bearer"
    user: GitHubUser


class UserResponse(BaseModel):
    """Current authenticated user info."""

    authenticated: bool
    user: GitHubUser | None = None
    is_contributor: bool = False
