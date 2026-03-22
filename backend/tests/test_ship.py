import pytest
from app.modules.ship.service import compute_level_from_essence
from app.modules.ship.models import LEVEL_THRESHOLDS


# --- Unit tests for threshold logic ---

def test_level_thresholds_length():
    assert len(LEVEL_THRESHOLDS) == 20


def test_compute_level_at_zero():
    assert compute_level_from_essence(0) == 1


def test_compute_level_at_threshold():
    assert compute_level_from_essence(5) == 2
    assert compute_level_from_essence(10) == 3
    assert compute_level_from_essence(20) == 5


def test_compute_level_just_below_threshold():
    assert compute_level_from_essence(4) == 1
    assert compute_level_from_essence(9) == 2


def test_compute_level_max():
    assert compute_level_from_essence(776) == 20
    assert compute_level_from_essence(9999) == 20


# --- API tests ---

def test_get_ship_lazy_creates(client, campaign, player_auth_headers):
    """GET /api/ship/ auto-creates the ship if none exists."""
    res = client.get("/api/ship/", headers=player_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "The Ship"
    assert data["level"] == 1
    assert data["essence"] == 0
    assert data["status"] == "critical"
    assert data["long_rest_cost"] == 2
    assert data["next_threshold"] == 5
    assert data["essence_to_next_level"] == 5


def test_get_ship_unauthenticated(client, campaign):
    res = client.get("/api/ship/")
    assert res.status_code == 401


def test_update_ship_admin(client, campaign, admin_auth_headers):
    res = client.put(
        "/api/ship/",
        json={"name": "The Ironclad", "level": 3, "essence": 12, "motd": "Ready to sail!"},
        headers=admin_auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "The Ironclad"
    assert data["level"] == 3
    assert data["essence"] == 12
    assert data["motd"] == "Ready to sail!"


def test_update_ship_player_forbidden(client, campaign, player_auth_headers):
    res = client.put(
        "/api/ship/",
        json={"name": "Stolen Ship"},
        headers=player_auth_headers,
    )
    assert res.status_code == 403


def test_adjust_ship_essence(client, campaign, admin_auth_headers):
    # Set initial state
    client.put("/api/ship/", json={"essence": 20}, headers=admin_auth_headers)

    res = client.post(
        "/api/ship/adjust",
        json={"essence_delta": 16, "description": "Mission reward"},
        headers=admin_auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["essence"] == 36
    # Should have leveled up: 36 >= threshold for level 6 (index 5 = 36)
    assert data["level"] == 6


def test_adjust_ship_essence_cannot_go_below_zero(client, campaign, admin_auth_headers):
    client.put("/api/ship/", json={"essence": 5}, headers=admin_auth_headers)
    res = client.post(
        "/api/ship/adjust",
        json={"essence_delta": -100, "description": "Big spend"},
        headers=admin_auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["essence"] == 0


def test_adjust_ship_player_forbidden(client, campaign, player_auth_headers):
    res = client.post(
        "/api/ship/adjust",
        json={"essence_delta": 10, "description": "Sneaky gain"},
        headers=player_auth_headers,
    )
    assert res.status_code == 403


def test_ship_status_nominal(client, campaign, admin_auth_headers):
    client.put("/api/ship/", json={"essence": 10}, headers=admin_auth_headers)
    res = client.get("/api/ship/", headers=admin_auth_headers)
    assert res.json()["status"] == "nominal"  # long_rest_cost=2 at level 1, essence=10


def test_ship_status_low(client, campaign, admin_auth_headers):
    # Set level explicitly and essence below long_rest_cost
    client.put("/api/ship/", json={"level": 5, "essence": 3}, headers=admin_auth_headers)
    res = client.get("/api/ship/", headers=admin_auth_headers)
    assert res.json()["status"] == "low"  # long_rest_cost=4 at level 5, essence=3


def test_ship_status_critical(client, campaign, admin_auth_headers):
    client.put("/api/ship/", json={"essence": 0}, headers=admin_auth_headers)
    res = client.get("/api/ship/", headers=admin_auth_headers)
    assert res.json()["status"] == "critical"


def test_level_auto_advances_on_adjust(client, campaign, admin_auth_headers):
    """Adjusting essence past a threshold auto-advances the level."""
    client.put("/api/ship/", json={"essence": 0, "level": 1}, headers=admin_auth_headers)
    res = client.post(
        "/api/ship/adjust",
        json={"essence_delta": 10, "description": "Earned essence"},
        headers=admin_auth_headers,
    )
    data = res.json()
    assert data["essence"] == 10
    assert data["level"] == 3  # thresholds: 0→L1, 5→L2, 10→L3


def test_level_never_decreases_on_spend(client, campaign, admin_auth_headers):
    """Level does not drop when essence is spent below the threshold."""
    # Set to level 3 with 10 essence
    client.put("/api/ship/", json={"essence": 10, "level": 3}, headers=admin_auth_headers)
    res = client.post(
        "/api/ship/adjust",
        json={"essence_delta": -8, "description": "Long rest"},
        headers=admin_auth_headers,
    )
    data = res.json()
    assert data["essence"] == 2
    assert data["level"] == 3  # still level 3


def test_long_rest_cost_by_tier(client, campaign, admin_auth_headers):
    for level, expected_cost in [(1, 2), (4, 2), (5, 4), (10, 4), (11, 6), (16, 6), (17, 8), (20, 8)]:
        client.put("/api/ship/", json={"level": level}, headers=admin_auth_headers)
        res = client.get("/api/ship/", headers=admin_auth_headers)
        assert res.json()["long_rest_cost"] == expected_cost, f"Level {level} should cost {expected_cost}"


def test_next_threshold_and_essence_to_next_level(client, campaign, admin_auth_headers):
    client.put("/api/ship/", json={"level": 2, "essence": 7}, headers=admin_auth_headers)
    res = client.get("/api/ship/", headers=admin_auth_headers)
    data = res.json()
    assert data["next_threshold"] == 10  # level 3 threshold
    assert data["essence_to_next_level"] == 3  # 10 - 7


def test_next_threshold_at_max_level(client, campaign, admin_auth_headers):
    client.put("/api/ship/", json={"level": 20, "essence": 776}, headers=admin_auth_headers)
    res = client.get("/api/ship/", headers=admin_auth_headers)
    data = res.json()
    assert data["next_threshold"] is None
    assert data["essence_to_next_level"] == 0


def test_adjust_creates_ledger_entry(client, campaign, admin_auth_headers):
    client.post(
        "/api/ship/adjust",
        json={"essence_delta": 10, "description": "Reward"},
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
    client.put("/api/ship/", json={"name": "Campaign 1 Ship", "essence": 999}, headers=admin_auth_headers)

    # Other campaign has its own ship (default values)
    res = client.get("/api/ship/", headers=other_headers)
    assert res.status_code == 200
    assert res.json()["name"] == "The Ship"
    assert res.json()["essence"] == 0
