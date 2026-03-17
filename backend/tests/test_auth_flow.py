"""
Auth flow integration tests.

Covers:
- Discord OAuth login redirect
- Discord OAuth callback (mocked Discord API)
- JWT claim validation in dependencies
- Global vs campaign-scoped token enforcement
"""
from unittest.mock import patch, MagicMock
from jose import jwt
from app.config import get_settings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _MockResponse:
    def __init__(self, status_code: int, data: dict):
        self.status_code = status_code
        self._data = data
        self.text = str(data)

    def json(self):
        return self._data


class _MockHttpxClient:
    """Async context manager that mocks both POST and GET calls to the Discord API."""

    def __init__(self, post_status=200, get_status=200):
        self._post_response = _MockResponse(
            post_status,
            {"access_token": "disc_access_token"} if post_status == 200 else {"error": "invalid_grant"},
        )
        self._get_response = _MockResponse(
            get_status,
            {"id": "disc123", "username": "HeroUser", "avatar": "avhash"} if get_status == 200 else {},
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def post(self, *args, **kwargs):
        return self._post_response

    async def get(self, *args, **kwargs):
        return self._get_response


def _patch_httpx(post_status=200, get_status=200):
    """Return a patch context manager for httpx.AsyncClient in auth router."""
    mock_client = _MockHttpxClient(post_status=post_status, get_status=get_status)
    return patch("app.modules.auth.router.httpx.AsyncClient", return_value=mock_client)


# ---------------------------------------------------------------------------
# Discord login redirect
# ---------------------------------------------------------------------------

class TestDiscordLoginRedirect:
    def test_redirects_to_discord(self, client):
        r = client.get("/api/auth/discord/login", follow_redirects=False)
        assert r.status_code in (302, 307)
        assert "discord.com/api/oauth2/authorize" in r.headers["location"]

    def test_redirect_contains_effective_redirect_uri(self, client):
        settings = get_settings()
        r = client.get("/api/auth/discord/login", follow_redirects=False)
        assert settings.DISCORD_REDIRECT_URI in r.headers["location"]

    def test_sets_return_to_cookie_for_relative_path(self, client):
        r = client.get("/api/auth/discord/login?return_to=/dashboard", follow_redirects=False)
        assert "auth_return_to" in r.cookies

    def test_does_not_set_cookie_for_disallowed_domain(self, client):
        r = client.get(
            "/api/auth/discord/login?return_to=https://evil.com/steal",
            follow_redirects=False,
        )
        assert "auth_return_to" not in r.cookies


# ---------------------------------------------------------------------------
# Discord OAuth callback
# ---------------------------------------------------------------------------

class TestDiscordCallback:
    def test_successful_callback_redirects_to_frontend(self, client):
        with _patch_httpx():
            r = client.get("/api/auth/discord/callback?code=validcode", follow_redirects=False)
        assert r.status_code in (302, 307)
        assert "/login/callback" in r.headers["location"]
        assert "token=" in r.headers["location"]

    def test_callback_jwt_contains_discord_id_and_global_type(self, client):
        with _patch_httpx():
            r = client.get("/api/auth/discord/callback?code=validcode", follow_redirects=False)
        location = r.headers["location"]
        # Extract token from query string
        token = next(
            part.split("=", 1)[1]
            for part in location.split("?", 1)[1].split("&")
            if part.startswith("token=")
        )
        settings = get_settings()
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "disc123"
        assert payload["type"] == "global"

    def test_token_exchange_failure_returns_400(self, client):
        with _patch_httpx(post_status=401):
            r = client.get("/api/auth/discord/callback?code=badcode", follow_redirects=False)
        assert r.status_code == 400

    def test_user_info_failure_returns_400(self, client):
        with _patch_httpx(get_status=401):
            r = client.get("/api/auth/discord/callback?code=goodcode", follow_redirects=False)
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# JWT dependency enforcement
# ---------------------------------------------------------------------------

class TestJWTDependencies:
    def test_campaign_endpoint_rejects_global_token(self, client, global_token):
        """A global token (no campaign_id) must be rejected on /api/auth/me."""
        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {global_token}"})
        assert r.status_code == 401

    def test_campaign_endpoint_accepts_valid_campaign_token(self, client, player_auth_headers):
        """/api/auth/me should return 200 for a valid campaign-scoped token."""
        r = client.get("/api/auth/me", headers=player_auth_headers)
        assert r.status_code == 200

    def test_garbage_token_returns_401(self, client):
        r = client.get("/api/auth/me", headers={"Authorization": "Bearer not.a.real.token"})
        assert r.status_code == 401

    def test_no_token_returns_401(self, client):
        r = client.get("/api/auth/me")
        assert r.status_code == 401

    def test_admin_endpoint_rejects_player(self, client, player_auth_headers):
        """Admin-only endpoints must reject players."""
        r = client.get("/api/admin/export", headers=player_auth_headers)
        assert r.status_code == 403

    def test_admin_endpoint_accepts_admin(self, client, admin_auth_headers):
        """Admin-only endpoints should return 200 for admin users."""
        r = client.get("/api/admin/export", headers=admin_auth_headers)
        assert r.status_code == 200
