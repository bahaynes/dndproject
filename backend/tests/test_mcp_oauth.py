"""MCP OAuth authorization server: metadata, /authorize -> consent -> Discord -> code, /token, /revoke."""
import base64
import hashlib
import json
import re
from html import unescape
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import parse_qs, urlencode, urlparse

import httpx
import pytest

from app.config import get_settings
from app.modules.oauth import models as oauth_models
from app.modules.oauth import tokens as oauth_tokens

CLIENT_ID = "https://client.example.com/oauth/client.json"
REDIRECT_URI = "http://localhost:33418/callback"
VERIFIER = "v" * 64


def _challenge(verifier: str = VERIFIER) -> str:
    return base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()


def _document(**overrides):
    doc = {
        "client_id": CLIENT_ID,
        "client_name": "Claude Code",
        "redirect_uris": [REDIRECT_URI],
        "token_endpoint_auth_method": "none",
    }
    doc.update(overrides)
    return doc


PINNED_ADDRESS = "93.184.215.14"


def _wire(status: int, body: bytes, headers=None) -> httpx.Response:
    """A response still on the wire (unread), like a real one."""
    return httpx.Response(status, stream=httpx.ByteStream(body), headers=headers)


def _serve(handler):
    """Stubs DNS (one public address) and the HTTP transport under the real cimd.fetch_document."""
    def make_client(**kwargs):
        return httpx.AsyncClient(transport=httpx.MockTransport(handler), **kwargs)

    return (
        patch("app.modules.oauth.cimd._check_host_is_public", AsyncMock(return_value=PINNED_ADDRESS)),
        patch("app.modules.oauth.cimd._http_client", side_effect=make_client),
    )


@pytest.fixture
def cimd_document():
    """Serves the client's metadata document over a stubbed network. Tests can mutate the dict before use."""
    doc = _document()

    def handler(request: httpx.Request) -> httpx.Response:
        return _wire(200, json.dumps(doc).encode(), {"Content-Type": "application/json"})

    dns, http = _serve(handler)
    with dns, http:
        yield doc


def _discord_mock(discord_id="gm_discord_1", username="GMUser"):
    def make_response(status, payload):
        r = MagicMock()
        r.status_code = status
        r.json.return_value = payload
        return r

    client = MagicMock()
    client.post = AsyncMock(return_value=make_response(200, {"access_token": "discord-access"}))
    client.get = AsyncMock(return_value=make_response(200, {"id": discord_id, "username": username}))
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return patch("app.modules.oauth.router.httpx.AsyncClient", return_value=client)


@pytest.fixture
def gm(db_session, campaign):
    from app.modules.auth import models as auth_models
    user = auth_models.User(username="GMUser", discord_id="gm_discord_1", campaign_id=campaign.id, role="admin")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _authorize_params(**overrides):
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "board:read board:write",
        "state": "client-state-1",
        "code_challenge": _challenge(),
        "code_challenge_method": "S256",
        "resource": get_settings().mcp_resource_url,
    }
    params.update(overrides)
    return {k: v for k, v in params.items() if v is not None}


def _forms(html: str) -> list[tuple[str, dict]]:
    forms = []
    for m in re.finditer(r'<form method="post" action="([^"]+)">(.*?)</form>', html, re.S):
        fields = {unescape(k): unescape(v) for k, v in re.findall(r'name="([^"]*)" value="([^"]*)"', m.group(2))}
        forms.append((unescape(m.group(1)), fields))
    return forms


def _submit(client, html: str, **match):
    """POSTs the page's form whose hidden fields include ``match``."""
    action, fields = next(
        (a, f) for a, f in _forms(html) if all(f.get(k) == str(v) for k, v in match.items())
    )
    return client.post(action, data=fields, follow_redirects=False)


def _next_location(r) -> str:
    """Where the browser goes next: a redirect, or the continuation page a POST answers with."""
    if r.status_code == 302:
        return r.headers["location"]
    assert r.status_code == 200, r.text
    m = re.search(r'http-equiv="refresh" content="0;url=([^"]+)"', r.text)
    assert m, r.text
    return unescape(m.group(1))


def _start_discord(client, **param_overrides) -> str:
    """/authorize and the client consent page. Returns the Discord state."""
    r = client.get("/api/oauth/authorize", params=_authorize_params(**param_overrides), follow_redirects=False)
    if r.status_code == 200:
        r = _submit(client, r.text, decision="approve")
    location = _next_location(r)
    assert location.startswith("https://discord.com/api/oauth2/authorize")
    return _query(location)["state"]


def _discord_callback(client, state):
    with _discord_mock():
        return client.get("/api/oauth/discord/callback", params={"code": "dc", "state": state}, follow_redirects=False)


def _query(url: str) -> dict:
    return {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}


def run_authorization(client, campaign_id, **param_overrides) -> dict:
    """Drives the browser side of the flow and returns the client's redirect query."""
    r = _discord_callback(client, _start_discord(client, **param_overrides))
    if r.status_code == 200:
        r = _submit(client, r.text, campaign_id=campaign_id)
    location = _next_location(r)
    assert location.startswith(REDIRECT_URI), location
    assert parse_qs(urlparse(location).query)["iss"] == [get_settings().public_origin]
    return _query(location)


def exchange_code(client, code, verifier=VERIFIER, **overrides):
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "code_verifier": verifier,
        "resource": get_settings().mcp_resource_url,
    }
    data.update(overrides)
    return client.post("/api/oauth/token", data={k: v for k, v in data.items() if v is not None})


def refresh(client, refresh_token, **overrides):
    data = {"grant_type": "refresh_token", "refresh_token": refresh_token, "client_id": CLIENT_ID}
    data.update(overrides)
    return client.post("/api/oauth/token", data=data)


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------

class TestMetadata:
    def test_authorization_server_metadata(self, client):
        r = client.get("/.well-known/oauth-authorization-server")
        assert r.status_code == 200
        data = r.json()
        origin = get_settings().public_origin
        assert data["issuer"] == origin
        assert data["authorization_endpoint"] == f"{origin}/api/oauth/authorize"
        assert data["code_challenge_methods_supported"] == ["S256"]
        assert data["token_endpoint_auth_methods_supported"] == ["none"]
        assert data["client_id_metadata_document_supported"] is True
        assert data["authorization_response_iss_parameter_supported"] is True
        assert "registration_endpoint" not in data

    def test_protected_resource_metadata(self, client):
        r = client.get("/.well-known/oauth-protected-resource/api/mcp")
        assert r.status_code == 200
        data = r.json()
        assert data["resource"] == get_settings().mcp_resource_url
        assert data["authorization_servers"] == [get_settings().public_origin]
        assert data["scopes_supported"] == ["board:read", "board:write"]
        assert "offline_access" not in data["scopes_supported"]


# ---------------------------------------------------------------------------
# /authorize validation
# ---------------------------------------------------------------------------

class TestAuthorizeValidation:
    def test_client_id_must_be_https_url(self, client, cimd_document):
        r = client.get("/api/oauth/authorize", params=_authorize_params(client_id="my-client"), follow_redirects=False)
        assert r.status_code == 400
        assert "location" not in r.headers

    def test_cimd_client_id_mismatch_rejected_without_redirect(self, client, cimd_document):
        cimd_document["client_id"] = "https://evil.example.com/client.json"
        r = client.get("/api/oauth/authorize", params=_authorize_params(), follow_redirects=False)
        assert r.status_code == 400
        assert "different client_id" in r.text
        assert "location" not in r.headers

    def test_redirect_uri_not_in_document_rejected_without_redirect(self, client, cimd_document):
        r = client.get(
            "/api/oauth/authorize",
            params=_authorize_params(redirect_uri="https://attacker.example.com/cb"),
            follow_redirects=False,
        )
        assert r.status_code == 400
        assert "location" not in r.headers

    def test_plain_http_redirect_to_non_localhost_rejected(self, client, cimd_document):
        cimd_document["redirect_uris"] = ["http://client.example.com/cb"]
        r = client.get(
            "/api/oauth/authorize",
            params=_authorize_params(redirect_uri="http://client.example.com/cb"),
            follow_redirects=False,
        )
        assert r.status_code == 400
        assert "location" not in r.headers

    def test_missing_pkce_redirects_with_error_and_iss(self, client, cimd_document):
        r = client.get(
            "/api/oauth/authorize",
            params=_authorize_params(code_challenge=None, code_challenge_method=None),
            follow_redirects=False,
        )
        assert r.status_code == 302
        q = _query(r.headers["location"])
        assert q["error"] == "invalid_request"
        assert q["state"] == "client-state-1"
        assert q["iss"] == get_settings().public_origin

    def test_plain_pkce_rejected(self, client, cimd_document):
        r = client.get(
            "/api/oauth/authorize",
            params=_authorize_params(code_challenge_method="plain"),
            follow_redirects=False,
        )
        assert r.status_code == 302
        assert _query(r.headers["location"])["error"] == "invalid_request"

    def test_resource_mismatch_rejected_at_authorize(self, client, cimd_document):
        r = client.get(
            "/api/oauth/authorize",
            params=_authorize_params(resource="https://other.example.com/mcp"),
            follow_redirects=False,
        )
        assert r.status_code == 302
        assert _query(r.headers["location"])["error"] == "invalid_target"

    def test_unknown_scope_rejected(self, client, cimd_document):
        r = client.get(
            "/api/oauth/authorize", params=_authorize_params(scope="board:read admin:all"), follow_redirects=False
        )
        assert r.status_code == 302
        assert _query(r.headers["location"])["error"] == "invalid_scope"

    def test_consent_page_shows_client_and_redirect_host(self, client, cimd_document):
        r = client.get("/api/oauth/authorize", params=_authorize_params(), follow_redirects=False)
        assert r.status_code == 200
        assert "Claude Code" in r.text
        assert "localhost" in r.text
        assert "runs on your own computer" in r.text
        # Discord is not involved before the user consents to this client.
        assert "discord.com" not in r.text

    def test_cancel_on_consent_page_returns_access_denied(self, client, cimd_document):
        r = client.get("/api/oauth/authorize", params=_authorize_params(), follow_redirects=False)
        r = _submit(client, r.text, decision="deny")
        q = _query(_next_location(r))
        assert q["error"] == "access_denied"
        assert q["iss"] == get_settings().public_origin

    def test_consent_with_wrong_csrf_rejected(self, client, cimd_document):
        r = client.get("/api/oauth/authorize", params=_authorize_params(), follow_redirects=False)
        action, fields = next((a, f) for a, f in _forms(r.text) if f.get("decision") == "approve")
        r = client.post(action, data={**fields, "csrf": "wrong"}, follow_redirects=False)
        assert r.status_code == 400

    def test_consent_decision_is_not_a_get(self, client, cimd_document):
        r = client.get("/api/oauth/authorize", params=_authorize_params(), follow_redirects=False)
        _, fields = _forms(r.text)[0]
        assert client.get("/api/oauth/consent", params={**fields, "decision": "approve"}).status_code == 405

    def test_duplicate_resource_without_scope_rejected(self, client, cimd_document):
        resource = get_settings().mcp_resource_url
        params = list(_authorize_params(scope=None).items()) + [("resource", resource)]
        r = client.get("/api/oauth/authorize", params=params, follow_redirects=False)
        assert r.status_code == 302
        assert _query(r.headers["location"])["error"] == "invalid_target"


# ---------------------------------------------------------------------------
# Full flow and tokens
# ---------------------------------------------------------------------------

class TestCodeFlow:
    def test_full_flow_issues_tokens(self, client, cimd_document, gm, campaign):
        q = run_authorization(client, campaign.id)
        assert q["state"] == "client-state-1"
        assert q["iss"] == get_settings().public_origin

        r = exchange_code(client, q["code"])
        assert r.status_code == 200, r.text
        assert r.headers["cache-control"] == "no-store"
        body = r.json()
        assert body["token_type"] == "Bearer"
        assert body["scope"] == "board:read board:write"
        claims = oauth_tokens.decode_access_token(body["access_token"])
        assert claims["sub"] == str(gm.id)
        assert claims["campaign_id"] == campaign.id
        assert claims["aud"] == get_settings().mcp_resource_url
        assert body["refresh_token"]

    def test_wrong_pkce_verifier_rejected(self, client, cimd_document, gm, campaign):
        q = run_authorization(client, campaign.id)
        r = exchange_code(client, q["code"], verifier="w" * 64)
        assert r.status_code == 400
        assert r.json()["error"] == "invalid_grant"

    def test_resource_mismatch_rejected_at_token(self, client, cimd_document, gm, campaign):
        q = run_authorization(client, campaign.id)
        r = exchange_code(client, q["code"], resource="https://other.example.com/mcp")
        assert r.status_code == 400
        assert r.json()["error"] == "invalid_target"

    def test_code_reuse_revokes_the_grant(self, client, cimd_document, gm, campaign, db_session):
        q = run_authorization(client, campaign.id)
        first = exchange_code(client, q["code"])
        assert first.status_code == 200
        second = exchange_code(client, q["code"])
        assert second.status_code == 400
        grant = db_session.query(oauth_models.OAuthGrant).one()
        assert grant.revoked_at is not None
        # The refresh token from the first exchange is dead too.
        assert refresh(client, first.json()["refresh_token"]).status_code == 400

    def test_code_replay_without_verifier_does_not_revoke(self, client, cimd_document, gm, campaign, db_session):
        q = run_authorization(client, campaign.id)
        first = exchange_code(client, q["code"])
        assert first.status_code == 200
        assert exchange_code(client, q["code"], verifier="w" * 64).status_code == 400
        assert db_session.query(oauth_models.OAuthGrant).one().revoked_at is None
        assert refresh(client, first.json()["refresh_token"]).status_code == 200

    def test_token_params_in_query_string_ignored(self, client, cimd_document, gm, campaign):
        q = run_authorization(client, campaign.id)
        data = {"grant_type": "authorization_code", "code": q["code"], "redirect_uri": REDIRECT_URI,
                "client_id": CLIENT_ID, "resource": get_settings().mcp_resource_url}
        r = client.post("/api/oauth/token", params={"code_verifier": VERIFIER}, data=data)
        assert r.status_code == 400

    def test_refresh_with_two_resources_rejected(self, client, cimd_document, gm, campaign):
        q = run_authorization(client, campaign.id)
        tokens = exchange_code(client, q["code"]).json()
        resource = get_settings().mcp_resource_url
        body = urlencode([
            ("grant_type", "refresh_token"), ("refresh_token", tokens["refresh_token"]), ("client_id", CLIENT_ID),
            ("resource", resource), ("resource", resource),
        ])
        r = client.post("/api/oauth/token", content=body,
                        headers={"Content-Type": "application/x-www-form-urlencoded"})
        assert r.status_code == 400
        assert r.json()["error"] == "invalid_target"

    def test_refresh_reuse_by_another_client_does_not_revoke(self, client, cimd_document, gm, campaign, db_session):
        q = run_authorization(client, campaign.id)
        tokens = exchange_code(client, q["code"]).json()
        refresh(client, tokens["refresh_token"])
        other = "https://other.example.com/oauth/client.json"
        cimd_document["client_id"] = other
        r = refresh(client, tokens["refresh_token"], client_id=other)
        assert r.status_code == 400
        assert db_session.query(oauth_models.OAuthGrant).one().revoked_at is None

    def test_refresh_rotates(self, client, cimd_document, gm, campaign):
        q = run_authorization(client, campaign.id)
        tokens = exchange_code(client, q["code"]).json()
        r = refresh(client, tokens["refresh_token"])
        assert r.status_code == 200, r.text
        new = r.json()
        assert new["refresh_token"] != tokens["refresh_token"]
        assert refresh(client, new["refresh_token"]).status_code == 200

    def test_refresh_reuse_revokes_the_grant(self, client, cimd_document, gm, campaign, db_session):
        q = run_authorization(client, campaign.id)
        tokens = exchange_code(client, q["code"]).json()
        rotated = refresh(client, tokens["refresh_token"]).json()
        assert refresh(client, tokens["refresh_token"]).status_code == 400
        assert db_session.query(oauth_models.OAuthGrant).one().revoked_at is not None
        assert refresh(client, rotated["refresh_token"]).status_code == 400

    def test_refresh_cannot_widen_scope(self, client, cimd_document, gm, campaign):
        q = run_authorization(client, campaign.id, scope="board:read")
        tokens = exchange_code(client, q["code"]).json()
        assert tokens["scope"] == "board:read"
        r = refresh(client, tokens["refresh_token"], scope="board:read board:write")
        assert r.status_code == 400
        assert r.json()["error"] == "invalid_scope"

    def test_demoted_gm_cannot_refresh(self, client, cimd_document, gm, campaign, db_session):
        q = run_authorization(client, campaign.id)
        tokens = exchange_code(client, q["code"]).json()
        gm.role = "player"
        db_session.commit()
        r = refresh(client, tokens["refresh_token"])
        assert r.status_code == 400
        assert db_session.query(oauth_models.OAuthGrant).one().revoked_at is not None

    def test_player_gets_no_campaign(self, client, cimd_document, db_session, campaign):
        from app.modules.auth import models as auth_models
        db_session.add(auth_models.User(username="P", discord_id="gm_discord_1", campaign_id=campaign.id, role="player"))
        db_session.commit()
        r = _discord_callback(client, _start_discord(client))
        assert r.status_code == 302
        q = _query(r.headers["location"])
        assert q["error"] == "access_denied"

    def test_cannot_approve_a_campaign_you_are_not_gm_of(self, client, cimd_document, gm, campaign, db_session):
        from app.modules.campaigns import models as campaign_models
        other = campaign_models.Campaign(name="Campaign B", discord_guild_id="guild_b")
        db_session.add(other)
        db_session.commit()
        r = _discord_callback(client, _start_discord(client))
        assert r.status_code == 200  # the picker, offering only campaign A
        action, fields = _forms(r.text)[0]
        r = client.post(action, data={**fields, "campaign_id": str(other.id)}, follow_redirects=False)
        assert r.status_code == 403
        assert "You are not a GM of that campaign." in r.text
        assert db_session.query(oauth_models.OAuthCode).count() == 0
        assert db_session.query(oauth_models.OAuthConsent).count() == 0

    def test_second_approval_of_the_same_request_issues_nothing(self, client, cimd_document, gm, campaign, db_session):
        r = _discord_callback(client, _start_discord(client))
        picker = r.text
        first = _submit(client, picker, campaign_id=campaign.id)
        assert "code" in _query(_next_location(first))
        second = _submit(client, picker, campaign_id=campaign.id)
        assert second.status_code == 400
        assert "expired" in second.text
        assert db_session.query(oauth_models.OAuthCode).count() == 1

    def test_discord_network_error_asks_to_restart(self, client, cimd_document, gm, campaign):
        state = _start_discord(client)
        failing = MagicMock()
        failing.post = AsyncMock(side_effect=httpx.ConnectError("boom"))
        failing.__aenter__ = AsyncMock(return_value=failing)
        failing.__aexit__ = AsyncMock(return_value=False)
        with patch("app.modules.oauth.router.httpx.AsyncClient", return_value=failing):
            r = client.get("/api/oauth/discord/callback", params={"code": "dc", "state": state}, follow_redirects=False)
        assert r.status_code == 502
        assert "Start the connection again" in r.text

    def test_discord_callback_replay_rejected(self, client, cimd_document, gm, campaign):
        state = _start_discord(client)
        assert _discord_callback(client, state).status_code == 200  # picker
        assert _discord_callback(client, state).status_code == 400

    def test_two_connections_in_one_browser_both_finish(self, client, cimd_document, gm, campaign):
        first = _start_discord(client, state="a")
        second = _start_discord(client, state="b")
        for state, expected in ((first, "a"), (second, "b")):
            r = _discord_callback(client, state)
            if r.status_code == 200:
                r = _submit(client, r.text, campaign_id=campaign.id)
            assert _query(_next_location(r))["state"] == expected

    def test_live_discord_role_is_checked(self, client, cimd_document, gm, campaign):
        """With a bot token, a GM row alone isn't enough: Discord must still say GM."""
        from app.modules.campaigns import discord_roles

        settings = get_settings()
        with patch.object(settings, "DISCORD_BOT_TOKEN", "bot"), patch.object(
            discord_roles, "resolve_campaign_role", AsyncMock(return_value="player")
        ):
            r = _discord_callback(client, _start_discord(client))
        assert r.status_code == 302
        assert _query(r.headers["location"])["error"] == "access_denied"

    def test_discord_callback_needs_the_browser_that_started(self, client, cimd_document, gm, campaign):
        state = _start_discord(client)
        client.cookies.clear()
        assert _discord_callback(client, state).status_code == 400

    def test_reconnect_skips_both_consent_pages(self, client, cimd_document, gm, campaign):
        run_authorization(client, campaign.id)
        r = client.get("/api/oauth/authorize", params=_authorize_params(state="s2"), follow_redirects=False)
        assert r.status_code == 302
        assert r.headers["location"].startswith("https://discord.com/")
        r = _discord_callback(client, _query(r.headers["location"])["state"])
        assert r.status_code == 302
        q = _query(r.headers["location"])
        assert q["state"] == "s2" and q["code"]


class TestRevoke:
    def test_revoke_refresh_token_kills_grant(self, client, cimd_document, gm, campaign, db_session):
        q = run_authorization(client, campaign.id)
        tokens = exchange_code(client, q["code"]).json()
        r = client.post("/api/oauth/revoke", data={"token": tokens["refresh_token"], "client_id": CLIENT_ID})
        assert r.status_code == 200
        assert db_session.query(oauth_models.OAuthGrant).one().revoked_at is not None
        assert refresh(client, tokens["refresh_token"]).status_code == 400

    def test_revoke_unknown_token_is_ok(self, client, cimd_document):
        r = client.post("/api/oauth/revoke", data={"token": "nope", "client_id": CLIENT_ID})
        assert r.status_code == 200


class TestCimdFetch:
    """The real fetcher, with the network stubbed."""

    @pytest.mark.asyncio
    async def test_private_address_refused(self):
        from app.modules.oauth import cimd

        async def fake_getaddrinfo(host, port, **kwargs):
            return [(None, None, None, None, ("10.0.0.5", 0))]

        loop = MagicMock()
        loop.getaddrinfo = fake_getaddrinfo
        with patch("app.modules.oauth.cimd.asyncio.get_running_loop", return_value=loop):
            with pytest.raises(cimd.CimdError, match="private"):
                await cimd.fetch_document("https://internal.example.com/client.json")

    @pytest.mark.asyncio
    async def test_connects_to_the_checked_address_with_the_real_hostname(self):
        from app.modules.oauth import cimd
        seen = {}

        def handler(request):
            seen.update(host=request.url.host, header=request.headers["host"], sni=request.extensions.get("sni_hostname"))
            return _wire(200, json.dumps(_document()).encode())

        dns, http = _serve(handler)
        with dns, http:
            await cimd.fetch_document(CLIENT_ID)
        assert seen == {"host": PINNED_ADDRESS, "header": "client.example.com", "sni": "client.example.com"}

    @pytest.mark.asyncio
    async def test_compressed_document_refused(self):
        import gzip
        from app.modules.oauth import cimd

        def handler(request):
            return _wire(200, gzip.compress(json.dumps(_document()).encode()), {"Content-Encoding": "gzip"})

        dns, http = _serve(handler)
        with dns, http, pytest.raises(cimd.CimdError, match="compressed"):
            await cimd.fetch_document(CLIENT_ID)

    @pytest.mark.asyncio
    async def test_oversized_document_refused(self):
        from app.modules.oauth import cimd

        def handler(request):
            return _wire(200, json.dumps(_document(padding="x" * 20000)).encode())

        dns, http = _serve(handler)
        with dns, http, pytest.raises(cimd.CimdError, match="too large"):
            await cimd.fetch_document(CLIENT_ID)

    @pytest.mark.asyncio
    async def test_total_deadline(self):
        import asyncio
        from app.modules.oauth import cimd

        class Drip(httpx.AsyncByteStream):
            async def __aiter__(self):
                while True:
                    await asyncio.sleep(0.02)
                    yield b" "

        def handler(request):
            return httpx.Response(200, stream=Drip())

        dns, http = _serve(handler)
        with dns, http, patch.object(cimd, "FETCH_TIMEOUT_SECONDS", 0.1), pytest.raises(cimd.CimdError, match="fetched"):
            await cimd.fetch_document(CLIENT_ID)

    def test_http_client_id_refused(self):
        from app.modules.oauth import cimd
        with pytest.raises(cimd.CimdError):
            cimd.validate_client_id_url("http://client.example.com/client.json")
