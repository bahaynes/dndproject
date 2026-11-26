"""Security regression tests covering auth, IDORs, validation, middleware, and hardening."""

import asyncio
from datetime import datetime, timezone

import pytest

from app import main as app_main
from app import security
from app.config import Settings, get_settings
from app.modules.campaigns import models as campaign_models
from app.modules.characters import models as char_models
from app.modules.items import models as item_models
from app.modules.maps import models as map_models
from app.modules.maps.earth_baker import _fetch_terrarium_grid
from app.modules.missions import models as mission_models
from app.modules.sessions import models as session_models
from conftest import _create_user_with_token


def _create_second_campaign_admin(db_session):
    other_camp = campaign_models.Campaign(name="Other Camp", discord_guild_id="other_guild_999")
    db_session.add(other_camp)
    db_session.commit()
    db_session.refresh(other_camp)
    other_admin, other_token = _create_user_with_token(
        db_session, "other_admin_999", "OtherAdmin", "admin", other_camp.id
    )
    return other_camp, other_admin, {"Authorization": f"Bearer {other_token}"}


# ---------------------------------------------------------------------------
# Configuration & Dev-Token Gate
# ---------------------------------------------------------------------------

def test_production_settings_rejects_default_or_short_secret_key():
    with pytest.raises(ValueError, match="SECRET_KEY"):
        Settings(
            APP_ENV="production",
            SECRET_KEY="a_very_secret_key_that_should_be_in_env_file",
            ENABLE_DEV_TOKEN=False,
            DATABASE_URL="sqlite:///./test.db",
            DISCORD_CLIENT_ID="cid",
            DISCORD_CLIENT_SECRET="csec",
        )

    with pytest.raises(ValueError, match="SECRET_KEY"):
        Settings(
            APP_ENV="production",
            SECRET_KEY="too_short",
            ENABLE_DEV_TOKEN=False,
            DATABASE_URL="sqlite:///./test.db",
            DISCORD_CLIENT_ID="cid",
            DISCORD_CLIENT_SECRET="csec",
        )


def test_production_settings_rejects_enable_dev_token():
    with pytest.raises(ValueError, match="ENABLE_DEV_TOKEN"):
        Settings(
            APP_ENV="production",
            SECRET_KEY="x" * 32,
            ENABLE_DEV_TOKEN=True,
            DATABASE_URL="sqlite:///./test.db",
            DISCORD_CLIENT_ID="cid",
            DISCORD_CLIENT_SECRET="csec",
        )


_DEV_SECRET = "s" * 40


def _settings_kwargs(**overrides):
    base = dict(
        SECRET_KEY="x" * 32,
        DATABASE_URL="sqlite:///./test.db",
        DISCORD_CLIENT_ID="cid",
        DISCORD_CLIENT_SECRET="csec",
    )
    base.update(overrides)
    return base


@pytest.mark.parametrize("app_env", ["development", "preview"])
@pytest.mark.parametrize("secret", ["", "too_short", " " * 40])
def test_enable_dev_token_requires_strong_secret(app_env, secret):
    with pytest.raises(ValueError, match="DEV_LOGIN_SECRET"):
        Settings(**_settings_kwargs(APP_ENV=app_env, ENABLE_DEV_TOKEN=True, DEV_LOGIN_SECRET=secret))


def test_production_rejects_enable_dev_token_even_with_secret():
    with pytest.raises(ValueError, match="ENABLE_DEV_TOKEN"):
        Settings(
            **_settings_kwargs(APP_ENV="production", ENABLE_DEV_TOKEN=True, DEV_LOGIN_SECRET=_DEV_SECRET)
        )


def test_dev_token_disabled_by_default_and_gated_by_env(client, monkeypatch):
    get_settings.cache_clear()
    try:
        r_status = client.get("/api/auth/dev-status")
        assert r_status.status_code == 200
        assert r_status.json() == {"dev_login_enabled": False}

        r_tok = client.post(
            "/api/auth/dev-token", json={}, headers={"X-Dev-Login-Secret": _DEV_SECRET}
        )
        assert r_tok.status_code == 404

        monkeypatch.setenv("ENABLE_DEV_TOKEN", "true")
        monkeypatch.setenv("APP_ENV", "development")
        monkeypatch.setenv("DEV_LOGIN_SECRET", _DEV_SECRET)
        get_settings.cache_clear()

        assert client.get("/api/auth/dev-status").json() == {"dev_login_enabled": True}

        # Missing and wrong secrets look exactly like a disabled endpoint
        r_none = client.post("/api/auth/dev-token", json={"role": "player"})
        assert r_none.status_code == 404
        r_wrong = client.post(
            "/api/auth/dev-token",
            json={"role": "player"},
            headers={"X-Dev-Login-Secret": "w" * 40},
        )
        assert r_wrong.status_code == 404
        assert r_wrong.json() == r_tok.json()

        r_ok = client.post(
            "/api/auth/dev-token",
            json={"role": "player"},
            headers={"X-Dev-Login-Secret": _DEV_SECRET},
        )
        assert r_ok.status_code == 200
        assert "access_token" in r_ok.json()
    finally:
        monkeypatch.delenv("ENABLE_DEV_TOKEN", raising=False)
        monkeypatch.delenv("APP_ENV", raising=False)
        monkeypatch.delenv("DEV_LOGIN_SECRET", raising=False)
        get_settings.cache_clear()


# ---------------------------------------------------------------------------
# Legacy Admin Removal
# ---------------------------------------------------------------------------

def test_legacy_admin_export_import_removed(client, admin_auth_headers):
    assert client.get("/api/admin/export", headers=admin_auth_headers).status_code == 404
    assert (
        client.post(
            "/api/admin/import",
            headers=admin_auth_headers,
            files={"file": ("data.json", b"{}", "application/json")},
        ).status_code
        == 404
    )


# ---------------------------------------------------------------------------
# IDOR, Cross-Campaign Isolation & Negative Quantity Checks
# ---------------------------------------------------------------------------

def test_character_endpoints_require_auth_and_campaign_scoping(
    client, db_session, campaign, player_auth_headers
):
    me = client.get("/api/auth/me", headers=player_auth_headers).json()
    char_id = me["characters"][0]["id"]

    # Unauthenticated read blocked
    assert client.get(f"/api/characters/{char_id}").status_code == 401

    # Cross-campaign admin cannot read, edit, set status, or delete
    _, _, other_admin_headers = _create_second_campaign_admin(db_session)
    assert client.get(f"/api/characters/{char_id}", headers=other_admin_headers).status_code == 404
    assert (
        client.put(
            f"/api/characters/{char_id}",
            json={"name": "Hijacked"},
            headers=other_admin_headers,
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/characters/{char_id}/status",
            json={"status": "Dead"},
            headers=other_admin_headers,
        ).status_code
        == 404
    )
    assert client.delete(f"/api/characters/{char_id}", headers=other_admin_headers).status_code == 404


def test_inventory_and_store_idor_and_negative_quantity_blocked(
    client, db_session, campaign, admin_auth_headers, player_auth_headers
):
    # Setup item, store listing, and inventory item in campaign 1
    item = item_models.Item(name="Potion", description="Heals", campaign_id=campaign.id)
    db_session.add(item)
    db_session.flush()
    store_item = item_models.StoreItem(item_id=item.id, price=50, quantity_available=10)
    db_session.add(store_item)
    me = client.get("/api/auth/me", headers=player_auth_headers).json()
    char_id = me["characters"][0]["id"]
    inv = item_models.InventoryItem(character_id=char_id, item_id=item.id, quantity=3)
    db_session.add(inv)
    db_session.commit()
    db_session.refresh(inv)
    db_session.refresh(store_item)

    # Another player in same campaign cannot delete this inventory item
    _, other_player_token = _create_user_with_token(
        db_session, "other_player_1", "OtherPlayer", "player", campaign.id
    )
    other_player_headers = {"Authorization": f"Bearer {other_player_token}"}
    assert (
        client.delete(
            f"/api/characters/{char_id}/inventory/{inv.id}",
            headers=other_player_headers,
        ).status_code
        == 403
    )

    # Cross-campaign admin cannot add or delete inventory on campaign 1's character
    other_camp, _, other_admin_headers = _create_second_campaign_admin(db_session)
    other_item = item_models.Item(name="Other Item", description="x", campaign_id=other_camp.id)
    db_session.add(other_item)
    db_session.commit()
    db_session.refresh(other_item)

    assert (
        client.post(
            f"/api/characters/{char_id}/inventory/?item_id={other_item.id}&quantity=1",
            headers=other_admin_headers,
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/characters/{char_id}/inventory/?item_id={other_item.id}&quantity=1",
            headers=admin_auth_headers,
        ).status_code
        == 404
    )
    assert (
        client.delete(
            f"/api/characters/{char_id}/inventory/{inv.id}",
            headers=other_admin_headers,
        ).status_code
        == 404
    )

    # Negative quantities rejected with 422 on inventory delete and store purchase
    assert (
        client.delete(
            f"/api/characters/{char_id}/inventory/{inv.id}?quantity=-5",
            headers=player_auth_headers,
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/api/store/items/{store_item.id}/purchase?quantity=-5",
            headers=player_auth_headers,
        ).status_code
        == 422
    )


def test_session_endpoints_enforce_campaign_scoping(
    client, db_session, campaign, admin_auth_headers, player_auth_headers
):
    miss = client.post(
        "/api/missions/",
        json={"name": "C1 Mission", "description": "d", "status": "Available", "rewards": []},
        headers=admin_auth_headers,
    ).json()
    sess = client.post(
        "/api/sessions/",
        json={"name": "C1 Session", "session_date": datetime.now(timezone.utc).isoformat()},
        headers=admin_auth_headers,
    ).json()
    client.post(f"/api/sessions/{sess['id']}/signup", headers=player_auth_headers)
    prop = client.post(
        "/api/sessions/proposals",
        json={"session_id": sess["id"], "mission_id": miss["id"]},
        headers=player_auth_headers,
    ).json()
    me = client.get("/api/auth/me", headers=player_auth_headers).json()
    char_id = me["characters"][0]["id"]

    _, _, other_admin_headers = _create_second_campaign_admin(db_session)
    assert (
        client.post(
            f"/api/sessions/proposals/{prop['id']}/toggle_back",
            headers=other_admin_headers,
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/sessions/proposals/{prop['id']}/force_confirm",
            headers=other_admin_headers,
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/sessions/proposals/{prop['id']}/veto",
            headers=other_admin_headers,
        ).status_code
        == 404
    )
    assert (
        client.delete(
            f"/api/sessions/{sess['id']}/kick/{char_id}",
            headers=other_admin_headers,
        ).status_code
        == 404
    )


# ---------------------------------------------------------------------------
# Privilege Escalation, URL Validation, Hidden Data & Inactive Users
# ---------------------------------------------------------------------------

def test_player_cannot_set_character_level_and_unsafe_urls_rejected(
    client, campaign, player_auth_headers, admin_auth_headers
):
    # Player creating a character with level=20 is forced to level 1
    created = client.post(
        "/api/characters/",
        json={"name": "Cheeky Novice", "level": 20},
        headers=player_auth_headers,
    )
    assert created.status_code == 200
    char_id = created.json()["id"]
    assert created.json()["level"] == 1

    # Player cannot raise level via PUT
    r_lvl = client.put(
        f"/api/characters/{char_id}",
        json={"level": 10},
        headers=player_auth_headers,
    )
    assert r_lvl.status_code == 403

    # Admin CAN update level
    r_adm = client.put(
        f"/api/characters/{char_id}",
        json={"level": 5},
        headers=admin_auth_headers,
    )
    assert r_adm.status_code == 200
    assert r_adm.json()["level"] == 5

    # Unsafe URL schemes rejected (422)
    assert (
        client.put(
            f"/api/characters/{char_id}",
            json={"character_sheet_url": "javascript:alert(1)"},
            headers=player_auth_headers,
        ).status_code
        == 422
    )
    assert (
        client.put(
            f"/api/characters/{char_id}",
            json={"image_url": "data:text/html,<script>alert(1)</script>"},
            headers=player_auth_headers,
        ).status_code
        == 422
    )

    # Unsafe TownLocation.link_path rejected (422)
    assert (
        client.put(
            "/api/ship/",
            json={
                "town_locations": [
                    {
                        "id": "bad-loc",
                        "name": "Trap",
                        "description": "xss",
                        "link_path": "javascript:alert(1)",
                    }
                ]
            },
            headers=admin_auth_headers,
        ).status_code
        == 422
    )
    assert (
        client.put(
            "/api/ship/",
            json={
                "town_locations": [
                    {
                        "id": "bad-proto-rel",
                        "name": "OpenRedirect",
                        "description": "evil",
                        "link_path": "//evil.example/phish",
                    }
                ]
            },
            headers=admin_auth_headers,
        ).status_code
        == 422
    )


def test_hidden_missions_and_dm_hex_notes_protected(
    client, db_session, campaign, admin_auth_headers, player_auth_headers
):
    # Hidden mission returns 404 to player, 200 to admin
    hidden = client.post(
        "/api/missions/",
        json={
            "name": "Secret Boss",
            "description": "Hidden",
            "is_discoverable": False,
            "rewards": [],
        },
        headers=admin_auth_headers,
    ).json()
    assert client.get(f"/api/missions/{hidden['id']}", headers=player_auth_headers).status_code == 404
    assert client.get(f"/api/missions/{hidden['id']}", headers=admin_auth_headers).status_code == 200

    # Retired mission returns 404 to player
    retired = client.post(
        "/api/missions/",
        json={
            "name": "Old Quest",
            "description": "Retired",
            "is_retired": True,
            "rewards": [],
        },
        headers=admin_auth_headers,
    ).json()
    assert client.get(f"/api/missions/{retired['id']}", headers=player_auth_headers).status_code == 404

    # Hex.notes stripped for player without mutating DB
    hmap = client.post(
        "/api/maps/",
        json={"name": "Secret Map", "width": 5, "height": 5},
        headers=admin_auth_headers,
    ).json()
    client.put(
        f"/api/maps/{hmap['id']}/hexes/0/0",
        json={"notes": "DM secret ambush"},
        headers=admin_auth_headers,
    )

    player_map = client.get(f"/api/maps/{hmap['id']}", headers=player_auth_headers).json()
    player_hex = next(h for h in player_map["hexes"] if h["q"] == 0 and h["r"] == 0)
    assert player_hex["notes"] is None

    player_maps = client.get("/api/maps/", headers=player_auth_headers).json()
    listed_map = next(m for m in player_maps if m["id"] == hmap["id"])
    listed_hex = next(h for h in listed_map["hexes"] if h["q"] == 0 and h["r"] == 0)
    assert listed_hex["notes"] is None

    admin_map = client.get(f"/api/maps/{hmap['id']}", headers=admin_auth_headers).json()
    admin_hex = next(h for h in admin_map["hexes"] if h["q"] == 0 and h["r"] == 0)
    assert admin_hex["notes"] == "DM secret ambush"


def test_inactive_user_rejected_across_endpoints(client, db_session, campaign):
    user, token = _create_user_with_token(
        db_session, "inactive_disc_1", "InactiveUser", "player", campaign.id
    )
    user.is_active = False
    db_session.commit()

    headers = {"Authorization": f"Bearer {token}"}
    for path in ("/api/auth/me", "/api/items/", "/api/missions/", "/api/sessions/", "/api/maps/"):
        assert client.get(path, headers=headers).status_code == 400

    global_tok = security.create_access_token(
        data={"sub": "inactive_disc_1", "type": "global", "username": "InactiveUser"}
    )
    r_login = client.post(
        "/api/campaigns/login",
        json={"campaign_id": campaign.id},
        headers={"Authorization": f"Bearer {global_tok}"},
    )
    assert r_login.status_code == 403


# ---------------------------------------------------------------------------
# OAuth State, Proxy Callback, CORS, Proxy Secret, Rate Limiter, Baker & Debug
# ---------------------------------------------------------------------------

def test_oauth_callback_and_proxy_callback_validation(client):
    # Missing or forged state rejected
    assert client.get("/api/auth/discord/callback?code=abc", follow_redirects=False).status_code == 400
    assert (
        client.get(
            "/api/auth/discord/callback?code=abc&state=tampered",
            follow_redirects=False,
        ).status_code
        == 400
    )

    # Login sets state + nonce cookie; removing cookie rejects callback
    r_login = client.get("/api/auth/discord/login", follow_redirects=False)
    from urllib.parse import parse_qs, urlparse

    state = parse_qs(urlparse(r_login.headers["location"]).query)["state"][0]
    client.cookies.clear()
    assert (
        client.get(
            f"/api/auth/discord/callback?code=abc&state={state}",
            follow_redirects=False,
        ).status_code
        == 400
    )

    # Proxy callback rejects arbitrary .run.app and javascript: schemes
    evil_state = security.create_access_token(
        data={
            "type": "oauth_state",
            "nonce": "n1",
            "callback": "https://evil.run.app/api/auth/discord/callback",
        }
    )
    assert (
        client.get(
            f"/api/auth/discord/proxy-callback?code=abc&state={evil_state}",
            follow_redirects=False,
        ).status_code
        == 400
    )

    js_state = security.create_access_token(
        data={
            "type": "oauth_state",
            "nonce": "n2",
            "callback": "javascript://dnd-frontend-pr-1-x-uc.a.run.app/api/auth/discord/callback",
        }
    )
    assert (
        client.get(
            f"/api/auth/discord/proxy-callback?code=abc&state={js_state}",
            follow_redirects=False,
        ).status_code
        == 400
    )

    # Valid PR Cloud Run frontend callback allowed
    pr_state = security.create_access_token(
        data={
            "type": "oauth_state",
            "nonce": "n3",
            "callback": "https://dnd-frontend-pr-42-abc123-uc.a.run.app/api/auth/discord/callback",
        }
    )
    r_pr = client.get(
        f"/api/auth/discord/proxy-callback?code=abc&state={pr_state}",
        follow_redirects=False,
    )
    assert r_pr.status_code in (302, 307)
    assert r_pr.headers["location"].startswith(
        "https://dnd-frontend-pr-42-abc123-uc.a.run.app/api/auth/discord/callback?"
    )


def test_cors_does_not_reflect_arbitrary_origin(client):
    r = client.get(
        "/api/v1/health",
        headers={"Origin": "https://evil.example"},
    )
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") is None


def test_proxy_shared_secret_middleware(client, monkeypatch):
    monkeypatch.setenv("PROXY_SHARED_SECRET", "super_shared_proxy_secret_value")
    get_settings.cache_clear()
    try:
        # Health check always stays reachable for Cloud Run / container probes
        assert client.get("/api/v1/health").status_code == 200

        # API route blocked without valid proxy secret
        assert client.get("/api/auth/dev-status").status_code == 403
        assert (
            client.get(
                "/api/auth/dev-status",
                headers={"X-Proxy-Secret": "wrong"},
            ).status_code
            == 403
        )

        # Matching proxy secret passes through middleware
        r_ok = client.get(
            "/api/auth/dev-status",
            headers={"X-Proxy-Secret": "super_shared_proxy_secret_value"},
        )
        assert r_ok.status_code == 200
    finally:
        monkeypatch.delenv("PROXY_SHARED_SECRET", raising=False)
        get_settings.cache_clear()


def test_rate_limiter_blocks_excess_auth_requests(client, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    get_settings.cache_clear()
    app_main._rate_limit_buckets.clear()
    try:
        for idx in range(60):
            # Spoofed leftmost X-Forwarded-For values must not bypass rate limiting
            r = client.get(
                "/api/auth/dev-status",
                headers={"X-Forwarded-For": f"198.51.100.{idx}, 203.0.113.99"},
            )
            assert r.status_code == 200
        r_limited = client.get(
            "/api/auth/dev-status",
            headers={"X-Forwarded-For": "198.51.100.250, 203.0.113.99"},
        )
        assert r_limited.status_code == 429
    finally:
        app_main._rate_limit_buckets.clear()
        monkeypatch.delenv("RATE_LIMIT_ENABLED", raising=False)
        get_settings.cache_clear()


def test_earth_baker_rejects_oversized_bbox():
    with pytest.raises(ValueError, match="too large"):
        asyncio.run(_fetch_terrarium_grid(-60.0, -170.0, 60.0, 170.0, zoom=5))


def test_debug_config_token_check(client, monkeypatch):
    monkeypatch.setenv("DEBUG_TOKEN", "debug_secret_token_123")
    get_settings.cache_clear()
    try:
        assert client.get("/api/debug/config", headers={"X-Debug-Token": "wrong"}).status_code == 403
        assert client.get("/api/debug/config", headers=[(b"x-debug-token", b"t\xf6k\xe9n")]).status_code == 403
        r_ok = client.get("/api/debug/config", headers={"X-Debug-Token": "debug_secret_token_123"})
        assert r_ok.status_code == 200
        assert "env_vars_set" in r_ok.json()
    finally:
        monkeypatch.delenv("DEBUG_TOKEN", raising=False)
        get_settings.cache_clear()


def test_coderabbit_followups_redaction_scoping_and_legacy_normalization(
    client, db_session, campaign, admin_auth_headers, player_auth_headers, monkeypatch
):
    from app.modules.ship import models as ship_models

    # 1. CharacterUpdate rejects explicit null for name/level but allows clearing description
    me = client.get("/api/auth/me", headers=player_auth_headers).json()
    char_id = me["characters"][0]["id"]
    assert client.put(f"/api/characters/{char_id}", json={"name": None}, headers=player_auth_headers).status_code == 422
    assert client.put(f"/api/characters/{char_id}", json={"level": None}, headers=admin_auth_headers).status_code == 422
    assert client.put(f"/api/characters/{char_id}", json={"description": None}, headers=player_auth_headers).status_code == 200

    # 2. WorldBundle rejects out-of-range store_quantity or map dimensions
    assert (
        client.post(
            "/api/admin/world/import",
            headers=admin_auth_headers,
            json={
                "bundle": {
                    "world_name": "Bad",
                    "items": [{"name": "Broken", "store_price": 1, "store_quantity": -2}],
                }
            },
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/admin/world/import",
            headers=admin_auth_headers,
            json={
                "bundle": {
                    "world_name": "Bad",
                    "maps": [{"name": "TooWide", "width": 201}],
                }
            },
        ).status_code
        == 422
    )

    # 3. add_hex_note redacts DM notes & hidden linked_mission; update_hex & sessions check campaign
    hidden_mission = client.post(
        "/api/missions/",
        json={"name": "Hidden Hex Quest", "description": "Secret", "is_discoverable": False, "rewards": []},
        headers=admin_auth_headers,
    ).json()
    hmap = client.post("/api/maps/", json={"name": "Redaction Map", "width": 5, "height": 5}, headers=admin_auth_headers).json()
    client.put(
        f"/api/maps/{hmap['id']}/hexes/0/0",
        json={"is_discovered": True, "notes": "DM secret", "linked_mission_id": hidden_mission["id"]},
        headers=admin_auth_headers,
    )
    r_note = client.post(
        f"/api/maps/{hmap['id']}/hexes/0/0/notes",
        json={"text": "Player saw tracks"},
        headers=player_auth_headers,
    )
    assert r_note.status_code == 200
    assert r_note.json()["notes"] is None
    assert r_note.json()["linked_mission"] is None

    # Cross-campaign mission rejected in update_hex and create_session
    other_camp, _, other_admin_headers = _create_second_campaign_admin(db_session)
    other_mission = client.post(
        "/api/missions/",
        json={"name": "Other Camp Quest", "description": "d", "rewards": []},
        headers=other_admin_headers,
    ).json()
    assert (
        client.put(
            f"/api/maps/{hmap['id']}/hexes/0/0",
            json={"linked_mission_id": other_mission["id"]},
            headers=admin_auth_headers,
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/sessions/",
            json={
                "name": "Cross Camp Session",
                "session_date": datetime.now(timezone.utc).isoformat(),
                "confirmed_mission_id": other_mission["id"],
            },
            headers=admin_auth_headers,
        ).status_code
        == 404
    )

    # Hidden mission confirmed on a session is redacted for players
    sess = client.post(
        "/api/sessions/",
        json={
            "name": "Hidden Mission Session",
            "session_date": datetime.now(timezone.utc).isoformat(),
            "confirmed_mission_id": hidden_mission["id"],
        },
        headers=admin_auth_headers,
    ).json()
    r_sess_player = client.get(f"/api/sessions/{sess['id']}", headers=player_auth_headers)
    assert r_sess_player.status_code == 200
    assert r_sess_player.json()["confirmed_mission"] is None
    assert r_sess_player.json()["confirmed_mission_id"] is None

    # 4. Legacy invalid link_path & character_sheet_url normalize on read instead of 500
    ship = ship_models.Ship(
        campaign_id=campaign.id,
        name="Legacy Hub",
        town_locations=[
            {"id": "legacy", "name": "Old", "description": "d", "link_path": "https://example.org"}
        ],
    )
    db_session.add(ship)
    char_obj = db_session.query(char_models.Character).filter_by(id=char_id).first()
    char_obj.character_sheet_url = "javascript:alert(1)"
    db_session.commit()

    r_ship = client.get("/api/ship/", headers=player_auth_headers)
    assert r_ship.status_code == 200
    assert r_ship.json()["town_locations"][0]["link_path"] is None

    r_char = client.get(f"/api/characters/{char_id}", headers=player_auth_headers)
    assert r_char.status_code == 200
    assert r_char.json()["character_sheet_url"] is None

    # 5. Deterministic Cloud Run preview host accepted in proxy-callback
    det_state = security.create_access_token(
        data={
            "type": "oauth_state",
            "nonce": "n_det",
            "callback": "https://dnd-frontend-pr-42-1234567890.us-central1.run.app/api/auth/discord/callback",
        }
    )
    r_det = client.get(
        f"/api/auth/discord/proxy-callback?code=abc&state={det_state}",
        follow_redirects=False,
    )
    assert r_det.status_code in (302, 307)

    # 6. Proxy secret supports PROXY_SHARED_SECRET_PREVIOUS rotation & rejects non-ASCII cleanly
    monkeypatch.setenv("PROXY_SHARED_SECRET", "new_secret")
    monkeypatch.setenv("PROXY_SHARED_SECRET_PREVIOUS", "old_secret")
    get_settings.cache_clear()
    try:
        assert client.get("/api/auth/dev-status", headers={"X-Proxy-Secret": "old_secret"}).status_code == 200
        assert client.get("/api/auth/dev-status", headers={"X-Proxy-Secret": "new_secret"}).status_code == 200
        assert client.get("/api/auth/dev-status", headers=[(b"x-proxy-secret", b"n\xf6n-ascii")]).status_code == 403
    finally:
        monkeypatch.delenv("PROXY_SHARED_SECRET", raising=False)
        monkeypatch.delenv("PROXY_SHARED_SECRET_PREVIOUS", raising=False)
        get_settings.cache_clear()

    # 7. Export succeeds for legacy out-of-range map width while import still rejects it
    wide_map = map_models.HexMap(
        campaign_id=campaign.id, name="Legacy Wide", width=250, height=20, hex_size=60
    )
    db_session.add(wide_map)
    db_session.commit()
    r_exp = client.get("/api/admin/world/export", headers=admin_auth_headers)
    assert r_exp.status_code == 200
    assert any(m["name"] == "Legacy Wide" and m["width"] == 250 for m in r_exp.json()["maps"])

    # 8. Session completion rejects cross-campaign mission; signup & toggle_back redact hidden mission
    assert (
        client.post(
            f"/api/sessions/{sess['id']}/complete",
            json={"result": "failure", "mission_id": other_mission["id"]},
            headers=admin_auth_headers,
        ).status_code
        == 404
    )
    r_signup = client.post(f"/api/sessions/{sess['id']}/signup", headers=player_auth_headers)
    assert r_signup.status_code == 200
    assert r_signup.json()["confirmed_mission"] is None

    hidden_prop = client.post(
        "/api/sessions/proposals",
        json={"session_id": sess["id"], "mission_id": hidden_mission["id"]},
        headers=admin_auth_headers,
    ).json()
    r_back = client.post(
        f"/api/sessions/proposals/{hidden_prop['id']}/toggle_back",
        headers=player_auth_headers,
    )
    assert r_back.status_code == 200
    assert r_back.json()["mission"] is None

    # 9. Production OAuth login behind Caddy proxy does not redirect-loop on matching X-Forwarded-Host
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "a" * 32)
    monkeypatch.setenv("ENABLE_DEV_TOKEN", "false")
    monkeypatch.setenv("FRONTEND_URL", "https://westmarches.bahaynes.com")
    get_settings.cache_clear()
    try:
        r_proxied = client.get(
            "/api/auth/discord/login",
            headers={"Host": "dnd-backend-123.run.app", "X-Forwarded-Host": "westmarches.bahaynes.com"},
            follow_redirects=False,
        )
        assert r_proxied.status_code in (302, 307)
        assert "discord.com/api/oauth2/authorize" in r_proxied.headers["location"]

        r_alt_host = client.get(
            "/api/auth/discord/login",
            headers={"Host": "dnd-backend-123.run.app", "X-Forwarded-Host": "dnd-frontend-123.run.app"},
            follow_redirects=False,
        )
        assert r_alt_host.status_code in (302, 307)
        assert r_alt_host.headers["location"] == "https://westmarches.bahaynes.com/api/auth/discord/login"
    finally:
        for var in ("APP_ENV", "SECRET_KEY", "ENABLE_DEV_TOKEN", "FRONTEND_URL"):
            monkeypatch.delenv(var, raising=False)
        get_settings.cache_clear()
