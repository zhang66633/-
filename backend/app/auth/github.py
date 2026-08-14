"""GitHub OAuth client — login flow + contributor verification."""

from __future__ import annotations

import logging
from urllib.parse import urlencode

import httpx

from .schemas import GitHubUser

logger = logging.getLogger(__name__)

# ── Allowed contributors ───────────────────────────────────────────

ALLOWED_CONTRIBUTORS: set[str] = {"zhang66633", "shu639"}

# ── GitHub OAuth URLs ──────────────────────────────────────────────

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_API = "https://api.github.com/user"


class GitHubOAuthClient:
    """Handles the GitHub OAuth web application flow."""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_authorize_url(self, state: str = "") -> str:
        """Build the GitHub OAuth authorize URL.

        The frontend redirects the user's browser to this URL.
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "read:user",
        }
        if state:
            params["state"] = state
        return f"{GITHUB_AUTHORIZE_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> tuple[str | None, str | None]:
        """Exchange an OAuth authorization code for a GitHub access token.

        Returns (access_token, error_message).  One of them is always None.
        """
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    GITHUB_TOKEN_URL,
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "code": code,
                        "redirect_uri": self.redirect_uri,
                    },
                    headers={"Accept": "application/json"},
                    timeout=15.0,
                )
                data = resp.json()
                if "access_token" in data:
                    return data["access_token"], None
                # GitHub returns error_description on failure
                err = data.get("error_description", data.get("error", "未知错误"))
                logger.error("GitHub OAuth token exchange failed: %s", err)
                return None, err
            except Exception as e:
                logger.exception("Failed to exchange GitHub OAuth code")
                return None, str(e)

    async def get_user(self, access_token: str) -> GitHubUser | None:
        """Fetch the authenticated user's GitHub profile.

        Returns a GitHubUser or None on failure.
        """
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    GITHUB_USER_API,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/json",
                    },
                    timeout=15.0,
                )
                resp.raise_for_status()
                data = resp.json()
                return GitHubUser(
                    id=data.get("id", 0),
                    login=data.get("login", ""),
                    name=data.get("name"),
                    email=data.get("email"),
                    avatar_url=data.get("avatar_url"),
                )
            except Exception:
                logger.exception("Failed to fetch GitHub user")
                return None

    def is_contributor(self, user: GitHubUser) -> bool:
        """Check if a GitHub user is in the allowed contributors list."""
        return user.login.lower() in {c.lower() for c in ALLOWED_CONTRIBUTORS}


# ── Module-level client ────────────────────────────────────────────

_oauth_client: GitHubOAuthClient | None = None


def get_oauth_client() -> GitHubOAuthClient:
    """Get or create the GitHub OAuth client singleton."""
    global _oauth_client
    from app.config import get_settings

    settings = get_settings()
    if _oauth_client is None:
        _oauth_client = GitHubOAuthClient(
            client_id=settings.github_client_id,
            client_secret=settings.github_client_secret,
            redirect_uri=settings.github_redirect_uri,
        )
    elif _oauth_client.redirect_uri != settings.github_redirect_uri:
        _oauth_client = GitHubOAuthClient(
            client_id=settings.github_client_id,
            client_secret=settings.github_client_secret,
            redirect_uri=settings.github_redirect_uri,
        )
    return _oauth_client
