import pytest


def test_get_ship_lazy_creates(client, campaign, player_auth_headers):
    """GET /api/ship/ auto-creates the ship if none exists."""
    res = client.get("/api/ship/", headers=player_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "The Ship"
    assert data["level"] == 1
    assert data["fuel"] == 100
    assert data["max_fuel"] == 100
    assert data["crystals"] == 0
    assert data["credits"] == 0
    assert data["status"] == "nominal"


def test_get_ship_unauthenticated(client, campaign):
    res = client.get("/api/ship/")
    assert res.status_code == 401


def test_update_ship_admin(client, campaign, admin_auth_headers):
    res = client.put(
        "/api/ship/",
        json={"name": "The Ironclad", "level": 3, "fuel": 60, "max_fuel": 100, "motd": "Ready to sail!"},
        headers=admin_auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "The Ironclad"
    assert data["level"] == 3
    assert data["motd"] == "Ready to sail!"


def test_update_ship_player_forbidden(client, campaign, player_auth_headers):
    res = client.put(
        "/api/ship/",
        json={"name": "Stolen Ship"},
        headers=player_auth_headers,
    )
    assert res.status_code == 403


def test_adjust_ship_resources(client, campaign, admin_auth_headers, player_auth_headers):
    # Set initial state
    client.put("/api/ship/", json={"fuel": 80, "max_fuel": 100, "crystals": 5, "credits": 200}, headers=admin_auth_headers)

    res = client.post(
        "/api/ship/adjust",
        json={"fuel_delta": -20, "crystal_delta": 3, "credit_delta": 100, "description": "Mission reward"},
        headers=admin_auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["fuel"] == 60
    assert data["crystals"] == 8
    assert data["credits"] == 300


def test_adjust_ship_player_forbidden(client, campaign, player_auth_headers):
    res = client.post(
        "/api/ship/adjust",
        json={"fuel_delta": 10, "description": "Sneaky gain"},
        headers=player_auth_headers,
    )
    assert res.status_code == 403


def test_ship_status_nominal(client, campaign, admin_auth_headers):
    client.put("/api/ship/", json={"fuel": 80, "max_fuel": 100}, headers=admin_auth_headers)
    res = client.get("/api/ship/", headers=admin_auth_headers)
    assert res.json()["status"] == "nominal"


def test_ship_status_low_fuel(client, campaign, admin_auth_headers):
    client.put("/api/ship/", json={"fuel": 40, "max_fuel": 100}, headers=admin_auth_headers)
    res = client.get("/api/ship/", headers=admin_auth_headers)
    assert res.json()["status"] == "low_fuel"


def test_ship_status_critical(client, campaign, admin_auth_headers):
    client.put("/api/ship/", json={"fuel": 10, "max_fuel": 100}, headers=admin_auth_headers)
    res = client.get("/api/ship/", headers=admin_auth_headers)
    assert res.json()["status"] == "critical"


def test_adjust_creates_ledger_entry(client, campaign, admin_auth_headers):
    client.post(
        "/api/ship/adjust",
        json={"fuel_delta": -10, "description": "Fuel burned"},
        headers=admin_auth_headers,
    )
    ledger = client.get("/api/ledger/", headers=admin_auth_headers)
    assert ledger.status_code == 200
    entries = ledger.json()
    assert len(entries) >= 1
    assert any(e["event_type"] == "AdminAdjustment" for e in entries)


def test_ship_scoped_to_campaign(client, db_session, campaign, admin_auth_headers):
    from conftest import _create_user_with_token
    from app.modules.campaigns import models as campaign_models

    other_camp = campaign_models.Campaign(name="Other Camp", discord_guild_id="888")
    db_session.add(other_camp)
    db_session.commit()
    db_session.refresh(other_camp)
    _, other_token = _create_user_with_token(db_session, "other_ship", "OtherShip", "admin", other_camp.id)
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # Update ship in original campaign
    client.put("/api/ship/", json={"name": "Campaign 1 Ship", "credits": 999}, headers=admin_auth_headers)

    # Other campaign has its own ship (default values)
    res = client.get("/api/ship/", headers=other_headers)
    assert res.status_code == 200
    assert res.json()["name"] == "The Ship"
    assert res.json()["credits"] == 0
