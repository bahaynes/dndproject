"""MCP resource server at /api/mcp: auth gate, scopes, tools, campaign scoping."""
import datetime
import json
from unittest.mock import patch

import jwt
import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.modules.auth import models as auth_models
from app.modules.mcp import server as mcp_server
from app.modules.missions import models as mission_models
from app.modules.oauth import models as oauth_models
from app.modules.oauth import server as oauth_server
from app.modules.oauth.tokens import utcnow

HEADERS = {
    "Accept": "application/json, text/event-stream",
    "Content-Type": "application/json",
    "MCP-Protocol-Version": "2025-06-18",
}


@pytest.fixture
def mcp_client(db_session):
    def provider():
        yield db_session

    original = mcp_server.db_provider
    mcp_server.db_provider = provider
    from app.dependencies import get_db
    app.dependency_overrides[get_db] = provider
    # The MCP transport only accepts known Host headers; TestClient's default "testserver" isn't one.
    with TestClient(app, base_url="http://localhost:8000") as c:
        yield c
    mcp_server.db_provider = original
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def gm(db_session, campaign):
    user = auth_models.User(username="GM", discord_id="gm_1", campaign_id=campaign.id, role="admin")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _token(db_session, user, scopes="board:read board:write"):
    grant = oauth_models.OAuthGrant(
        user_id=user.id, campaign_id=user.campaign_id, client_id="https://client.example.com/c.json",
        scopes=scopes, resource=get_settings().mcp_resource_url, created_at=utcnow(),
    )
    db_session.add(grant)
    db_session.flush()
    tokens = oauth_server.issue_tokens(db_session, grant, scopes)
    db_session.commit()
    return tokens["access_token"], grant


def _rpc(client, token, method, params=None, *, raw=False):
    headers = dict(HEADERS)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        body["params"] = params
    r = client.post("/api/mcp", json=body, headers=headers)
    return r if raw else r.json()


def _call(client, token, tool_name, **arguments):
    data = _rpc(client, token, "tools/call", {"name": tool_name, "arguments": arguments})
    result = data["result"]
    return result


def _ok(result):
    assert not result.get("isError"), result
    structured = result.get("structuredContent")
    if structured is not None:
        return structured.get("result", structured)
    return json.loads(result["content"][0]["text"])


# ---------------------------------------------------------------------------
# Gate
# ---------------------------------------------------------------------------

class TestAuthGate:
    def test_missing_token_gets_401_with_resource_metadata(self, mcp_client):
        r = _rpc(mcp_client, None, "tools/list", raw=True)
        assert r.status_code == 401
        header = r.headers["www-authenticate"]
        assert 'resource_metadata="http://localhost:8000/.well-known/oauth-protected-resource/api/mcp"' in header
        assert 'scope="board:read"' in header

    def test_frontend_jwt_rejected(self, mcp_client, admin_auth_headers):
        token = admin_auth_headers["Authorization"].split(" ", 1)[1]
        r = _rpc(mcp_client, token, "tools/list", raw=True)
        assert r.status_code == 401
        assert 'error="invalid_token"' in r.headers["www-authenticate"]

    def test_wrong_audience_rejected(self, mcp_client, db_session, gm):
        _, grant = _token(db_session, gm)
        settings = get_settings()
        forged = jwt.encode(
            {
                "iss": settings.public_origin, "sub": str(gm.id), "aud": "https://elsewhere.example.com/mcp",
                "campaign_id": gm.campaign_id, "client_id": grant.client_id, "grant_id": grant.id,
                "scope": "board:read", "typ": "mcp_access",
                "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=5),
            },
            settings.mcp_token_secret, algorithm="HS256",
        )
        assert _rpc(mcp_client, forged, "tools/list", raw=True).status_code == 401

    def test_mcp_token_rejected_by_the_rest_of_the_api(self, mcp_client, db_session, gm):
        token, _ = _token(db_session, gm)
        r = mcp_client.get("/api/missions/", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401

    def test_revoked_grant_rejected(self, mcp_client, db_session, gm):
        token, grant = _token(db_session, gm)
        grant.revoked_at = utcnow()
        db_session.commit()
        assert _rpc(mcp_client, token, "tools/list", raw=True).status_code == 401

    def test_demoted_gm_rejected(self, mcp_client, db_session, gm):
        token, _ = _token(db_session, gm)
        gm.role = "player"
        db_session.commit()
        assert _rpc(mcp_client, token, "tools/list", raw=True).status_code == 401

    def test_write_with_read_token_gets_403_insufficient_scope(self, mcp_client, db_session, gm):
        token, _ = _token(db_session, gm, scopes="board:read")
        r = _rpc(mcp_client, token, "tools/call", {"name": "create_mission", "arguments": {"name": "X"}}, raw=True)
        assert r.status_code == 403
        header = r.headers["www-authenticate"]
        assert 'error="insufficient_scope"' in header
        assert 'scope="board:read board:write"' in header
        assert db_session.query(mission_models.Mission).count() == 0

    def test_read_tool_with_read_token_allowed(self, mcp_client, db_session, gm):
        token, _ = _token(db_session, gm, scopes="board:read")
        assert _ok(_call(mcp_client, token, "list_missions")) == []

    def test_unknown_host_refused(self, db_session, gm):
        token, _ = _token(db_session, gm)

        def provider():
            yield db_session

        mcp_server.db_provider = provider
        try:
            with TestClient(app, base_url="http://evil.example.com") as c:
                r = _rpc(c, token, "tools/list", raw=True)
        finally:
            mcp_server.db_provider = mcp_server.get_db
        assert r.status_code == 421

    def test_disabled_in_production_without_secret(self, mcp_client):
        settings = get_settings()
        with patch.object(settings, "APP_ENV", "production"), patch.object(settings, "MCP_TOKEN_SECRET", ""):
            assert _rpc(mcp_client, None, "tools/list", raw=True).status_code == 503
            assert mcp_client.get("/.well-known/oauth-authorization-server").status_code == 503


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def _mission(db_session, campaign_id, **kw):
    m = mission_models.Mission(name=kw.pop("name", "M"), campaign_id=campaign_id, **kw)
    db_session.add(m)
    db_session.commit()
    db_session.refresh(m)
    return m


class TestReadTools:
    def test_tools_listed(self, mcp_client, db_session, gm):
        token, _ = _token(db_session, gm)
        names = {t["name"] for t in _rpc(mcp_client, token, "tools/list")["result"]["tools"]}
        assert names == {
            "list_missions", "get_mission", "list_sessions", "list_items", "list_factions",
            "create_mission", "update_mission", "set_mission_module",
        }

    def test_list_missions_is_campaign_scoped_and_includes_hidden(self, mcp_client, db_session, gm, campaign):
        from app.modules.campaigns import models as campaign_models
        other = campaign_models.Campaign(name="Other", discord_guild_id="other_guild")
        db_session.add(other)
        db_session.commit()
        _mission(db_session, campaign.id, name="Visible")
        _mission(db_session, campaign.id, name="Hidden", is_discoverable=False)
        _mission(db_session, other.id, name="Elsewhere")
        token, _ = _token(db_session, gm)
        names = {m["name"] for m in _ok(_call(mcp_client, token, "list_missions"))}
        assert names == {"Visible", "Hidden"}

    def test_get_mission_from_other_campaign_not_found(self, mcp_client, db_session, gm):
        from app.modules.campaigns import models as campaign_models
        other = campaign_models.Campaign(name="Other", discord_guild_id="other_guild_2")
        db_session.add(other)
        db_session.commit()
        foreign = _mission(db_session, other.id, name="Elsewhere")
        token, _ = _token(db_session, gm)
        result = _call(mcp_client, token, "get_mission", mission_id=foreign.id)
        assert result["isError"] is True

    def test_list_sessions_items_factions(self, mcp_client, db_session, gm):
        token, _ = _token(db_session, gm)
        assert _ok(_call(mcp_client, token, "list_sessions", upcoming_only=True)) == []
        assert _ok(_call(mcp_client, token, "list_items")) == []
        assert isinstance(_ok(_call(mcp_client, token, "list_factions")), list)


class TestWriteTools:
    def test_create_mission_is_forced_hidden(self, mcp_client, db_session, gm, campaign, player_auth_headers):
        token, _ = _token(db_session, gm)
        created = _ok(_call(mcp_client, token, "create_mission", name="Into the Barrow", tier="Tier 1",
                            foundry_module="oneshot-into-the-barrow"))
        assert created["is_discoverable"] is False
        assert created["foundry_module"] == "oneshot-into-the-barrow"
        # Players can't see it.
        r = mcp_client.get("/api/missions/", headers=player_auth_headers)
        assert all(m["name"] != "Into the Barrow" for m in r.json())

    def test_update_mission_keeps_visibility_status_and_rewards(self, mcp_client, db_session, gm, campaign):
        mission = _mission(db_session, campaign.id, name="Old", status="In-Progress", is_discoverable=True)
        db_session.add(mission_models.MissionReward(mission_id=mission.id, gold=50))
        db_session.commit()
        token, _ = _token(db_session, gm)
        updated = _ok(_call(mcp_client, token, "update_mission", mission_id=mission.id, name="New",
                            description="Rewritten"))
        assert updated["name"] == "New"
        assert updated["description"] == "Rewritten"
        assert updated["is_discoverable"] is True
        assert updated["status"] == "In-Progress"
        assert [r["gold"] for r in updated["rewards"]] == [50]

    def test_update_mission_rejects_foreign_prerequisite(self, mcp_client, db_session, gm, campaign):
        from app.modules.campaigns import models as campaign_models
        other = campaign_models.Campaign(name="Other", discord_guild_id="other_guild_3")
        db_session.add(other)
        db_session.commit()
        foreign = _mission(db_session, other.id)
        mine = _mission(db_session, campaign.id)
        token, _ = _token(db_session, gm)
        result = _call(mcp_client, token, "update_mission", mission_id=mine.id, prerequisite_id=foreign.id)
        assert result["isError"] is True

    def test_set_mission_module_validates_and_shows_on_mission(self, mcp_client, db_session, gm, campaign,
                                                               admin_auth_headers):
        mission = _mission(db_session, campaign.id)
        token, _ = _token(db_session, gm)
        bad = _call(mcp_client, token, "set_mission_module", mission_id=mission.id, module_id="../../etc")
        assert bad["isError"] is True
        _ok(_call(mcp_client, token, "set_mission_module", mission_id=mission.id, module_id="oneshot-gilded-moth"))
        r = mcp_client.get(f"/api/missions/{mission.id}", headers=admin_auth_headers)
        assert r.json()["foundry_module"] == "oneshot-gilded-moth"
        _ok(_call(mcp_client, token, "set_mission_module", mission_id=mission.id))
        db_session.refresh(mission)
        assert mission.foundry_module is None

    def test_update_via_rest_does_not_clear_module(self, mcp_client, db_session, gm, campaign, admin_auth_headers):
        mission = _mission(db_session, campaign.id, foundry_module="oneshot-x")
        r = mcp_client.put(f"/api/missions/{mission.id}", json={"name": "Renamed"}, headers=admin_auth_headers)
        assert r.status_code == 200
        assert r.json()["foundry_module"] == "oneshot-x"


class TestHostCheck:
    @pytest.mark.parametrize("host,ok", [
        ("westmarches.bahaynes.com", True),
        ("westmarches.bahaynes.com:443", True),
        ("dnd-backend-yh7tabjahq-uc.a.run.app", True),
        ("run.app", False),
        ("evilrun.app", False),
        ("localhost:8000", True),
        ("[::1]:8000", False),
        ("attacker.example.com", False),
        ("", False),
    ])
    def test_host_allowed(self, host, ok):
        allowed = ["localhost", "127.0.0.1", "westmarches.bahaynes.com", "*.run.app"]
        assert mcp_server.host_allowed(host, allowed) is ok

    def test_browser_origin_from_elsewhere_refused(self, mcp_client, db_session, gm):
        token, _ = _token(db_session, gm)
        r = mcp_client.post(
            "/api/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            headers={**HEADERS, "Authorization": f"Bearer {token}", "Origin": "https://evil.example.com"},
        )
        assert r.status_code == 403
