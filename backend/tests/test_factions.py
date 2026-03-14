import pytest


def test_get_reputations_initializes_both_factions(client, campaign, player_auth_headers):
    # get_all_reputations auto-creates Kathedral + Vastarei at level 0
    res = client.get("/api/factions/", headers=player_auth_headers)
    assert res.status_code == 200
    factions = {f["faction_name"]: f for f in res.json()}
    assert set(factions.keys()) == {"Kathedral", "Vastarei"}
    assert all(f["level"] == 0 for f in factions.values())


def test_get_reputations_unauthenticated(client, campaign):
    res = client.get("/api/factions/")
    assert res.status_code == 401


def test_adjust_reputation_admin(client, campaign, admin_auth_headers):
    res = client.post(
        "/api/factions/Kathedral/adjust",
        json={"delta": 1, "description": "Helped them out"},
        headers=admin_auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["faction_name"] == "Kathedral"
    assert data["level"] == 1
    assert len(data["events"]) == 1
    assert data["events"][0]["delta"] == 1


def test_adjust_reputation_player_forbidden(client, campaign, player_auth_headers):
    res = client.post(
        "/api/factions/Kathedral/adjust",
        json={"delta": 1, "description": "Sneaky adjust"},
        headers=player_auth_headers,
    )
    assert res.status_code == 403


def test_adjust_reputation_invalid_faction(client, campaign, admin_auth_headers):
    res = client.post(
        "/api/factions/InvalidFaction/adjust",
        json={"delta": 1, "description": "Doesn't matter"},
        headers=admin_auth_headers,
    )
    assert res.status_code == 400
    assert "Unknown faction" in res.json()["detail"]


def test_adjust_reputation_accumulates(client, campaign, admin_auth_headers, player_auth_headers):
    client.post(
        "/api/factions/Vastarei/adjust",
        json={"delta": 2, "description": "First"},
        headers=admin_auth_headers,
    )
    client.post(
        "/api/factions/Vastarei/adjust",
        json={"delta": -1, "description": "Second"},
        headers=admin_auth_headers,
    )
    res = client.get("/api/factions/", headers=player_auth_headers)
    vastarei = next(f for f in res.json() if f["faction_name"] == "Vastarei")
    assert vastarei["level"] == 1
    assert len(vastarei["events"]) == 2


def test_get_reputations_after_adjust(client, campaign, admin_auth_headers, player_auth_headers):
    client.post(
        "/api/factions/Kathedral/adjust",
        json={"delta": 3, "description": "Big win"},
        headers=admin_auth_headers,
    )
    res = client.get("/api/factions/", headers=player_auth_headers)
    kathedral = next(f for f in res.json() if f["faction_name"] == "Kathedral")
    assert kathedral["level"] == 3
    assert kathedral["events"][0]["description"] == "Big win"


def test_factions_scoped_to_campaign(client, db_session, campaign, admin_auth_headers):
    from conftest import _create_user_with_token
    from app.modules.campaigns import models as campaign_models

    other_camp = campaign_models.Campaign(name="Other Camp", discord_guild_id="777")
    db_session.add(other_camp)
    db_session.commit()
    db_session.refresh(other_camp)
    _, other_token = _create_user_with_token(db_session, "other_fac", "OtherFac", "admin", other_camp.id)
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # Adjust in original campaign
    client.post(
        "/api/factions/Kathedral/adjust",
        json={"delta": 5, "description": "Own campaign"},
        headers=admin_auth_headers,
    )

    # Other campaign has its own factions at 0 — unaffected by original campaign's adjustments
    res = client.get("/api/factions/", headers=other_headers)
    assert res.status_code == 200
    factions = {f["faction_name"]: f for f in res.json()}
    assert set(factions.keys()) == {"Kathedral", "Vastarei"}
    assert all(f["level"] == 0 for f in factions.values())
