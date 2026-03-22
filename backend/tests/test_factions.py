import pytest


def _create_faction(client, name, headers, color="#3b82f6"):
    res = client.post(
        "/api/factions/",
        json={"faction_name": name, "color": color, "description": f"{name} description"},
        headers=headers,
    )
    assert res.status_code == 200, res.json()
    return res.json()


def test_get_reputations_empty_initially(client, campaign, player_auth_headers):
    res = client.get("/api/factions/", headers=player_auth_headers)
    assert res.status_code == 200
    assert res.json() == []


def test_get_reputations_unauthenticated(client, campaign):
    res = client.get("/api/factions/")
    assert res.status_code == 401


def test_create_faction_admin(client, campaign, admin_auth_headers):
    data = _create_faction(client, "The Alliance", admin_auth_headers, color="#3b82f6")
    assert data["faction_name"] == "The Alliance"
    assert data["level"] == 0
    assert data["color"] == "#3b82f6"


def test_create_faction_player_forbidden(client, campaign, player_auth_headers):
    res = client.post(
        "/api/factions/",
        json={"faction_name": "Rogue", "color": "#ff0000"},
        headers=player_auth_headers,
    )
    assert res.status_code == 403


def test_create_faction_duplicate_rejected(client, campaign, admin_auth_headers):
    _create_faction(client, "The Rim", admin_auth_headers)
    res = client.post(
        "/api/factions/",
        json={"faction_name": "The Rim"},
        headers=admin_auth_headers,
    )
    assert res.status_code == 409


def test_adjust_reputation_admin(client, campaign, admin_auth_headers):
    _create_faction(client, "The Alliance", admin_auth_headers)
    res = client.post(
        "/api/factions/The Alliance/adjust",
        json={"delta": 1, "description": "Helped with transit permits"},
        headers=admin_auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["faction_name"] == "The Alliance"
    assert data["level"] == 1
    assert len(data["events"]) == 1
    assert data["events"][0]["delta"] == 1


def test_adjust_reputation_player_forbidden(client, campaign, admin_auth_headers, player_auth_headers):
    _create_faction(client, "The Alliance", admin_auth_headers)
    res = client.post(
        "/api/factions/The Alliance/adjust",
        json={"delta": 1, "description": "Sneaky adjust"},
        headers=player_auth_headers,
    )
    assert res.status_code == 403


def test_adjust_reputation_invalid_faction(client, campaign, admin_auth_headers):
    res = client.post(
        "/api/factions/NoSuchFaction/adjust",
        json={"delta": 1, "description": "Doesn't matter"},
        headers=admin_auth_headers,
    )
    assert res.status_code == 404


def test_adjust_reputation_accumulates(client, campaign, admin_auth_headers, player_auth_headers):
    _create_faction(client, "The Rim", admin_auth_headers)
    client.post(
        "/api/factions/The Rim/adjust",
        json={"delta": 2, "description": "First"},
        headers=admin_auth_headers,
    )
    client.post(
        "/api/factions/The Rim/adjust",
        json={"delta": -1, "description": "Second"},
        headers=admin_auth_headers,
    )
    res = client.get("/api/factions/", headers=player_auth_headers)
    rim = next(f for f in res.json() if f["faction_name"] == "The Rim")
    assert rim["level"] == 1
    assert len(rim["events"]) == 2


def test_get_reputations_after_adjust(client, campaign, admin_auth_headers, player_auth_headers):
    _create_faction(client, "The Alliance", admin_auth_headers)
    client.post(
        "/api/factions/The Alliance/adjust",
        json={"delta": 3, "description": "Big win"},
        headers=admin_auth_headers,
    )
    res = client.get("/api/factions/", headers=player_auth_headers)
    alliance = next(f for f in res.json() if f["faction_name"] == "The Alliance")
    assert alliance["level"] == 3
    assert alliance["events"][0]["description"] == "Big win"


def test_factions_scoped_to_campaign(client, db_session, campaign, admin_auth_headers):
    from conftest import _create_user_with_token
    from app.modules.campaigns import models as campaign_models

    _create_faction(client, "The Alliance", admin_auth_headers)
    client.post(
        "/api/factions/The Alliance/adjust",
        json={"delta": 5, "description": "Own campaign"},
        headers=admin_auth_headers,
    )

    # Other campaign starts with no factions
    other_camp = campaign_models.Campaign(name="Other Camp", discord_guild_id="777")
    db_session.add(other_camp)
    db_session.commit()
    db_session.refresh(other_camp)
    _, other_token = _create_user_with_token(db_session, "other_fac", "OtherFac", "admin", other_camp.id)
    other_headers = {"Authorization": f"Bearer {other_token}"}

    res = client.get("/api/factions/", headers=other_headers)
    assert res.status_code == 200
    assert res.json() == []


def test_delete_faction_admin(client, campaign, admin_auth_headers, player_auth_headers):
    _create_faction(client, "Temp Faction", admin_auth_headers)
    res = client.delete("/api/factions/Temp Faction", headers=admin_auth_headers)
    assert res.status_code == 204
    res = client.get("/api/factions/", headers=player_auth_headers)
    names = [f["faction_name"] for f in res.json()]
    assert "Temp Faction" not in names
