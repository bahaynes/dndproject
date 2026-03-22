import pytest
from datetime import datetime


def test_get_ledger_empty(client, campaign, player_auth_headers):
    res = client.get("/api/ledger/", headers=player_auth_headers)
    assert res.status_code == 200
    assert res.json() == []


def test_get_ledger_unauthenticated(client, campaign):
    res = client.get("/api/ledger/")
    assert res.status_code == 401


def test_admin_create_ledger_entry(client, campaign, admin_auth_headers):
    res = client.post(
        "/api/ledger/",
        json={
            "event_type": "AdminAdjustment",
            "description": "Manual essence award",
            "essence_delta": 20,
        },
        headers=admin_auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["event_type"] == "AdminAdjustment"
    assert data["essence_delta"] == 20
    assert data["campaign_id"] is not None
    assert data["ship_snapshot"] is not None  # snapshot captured at time of entry


def test_player_cannot_create_ledger_entry(client, campaign, player_auth_headers):
    res = client.post(
        "/api/ledger/",
        json={"event_type": "AdminAdjustment", "description": "Sneaky entry"},
        headers=player_auth_headers,
    )
    assert res.status_code == 403


def test_invalid_event_type_rejected(client, campaign, admin_auth_headers):
    res = client.post(
        "/api/ledger/",
        json={"event_type": "BogusEvent", "description": "Invalid"},
        headers=admin_auth_headers,
    )
    assert res.status_code == 400
    assert "event_type" in res.json()["detail"]


def test_ledger_entries_sorted_newest_first(client, campaign, admin_auth_headers):
    client.post("/api/ledger/", json={"event_type": "AdminAdjustment", "description": "First"}, headers=admin_auth_headers)
    client.post("/api/ledger/", json={"event_type": "AdminAdjustment", "description": "Second"}, headers=admin_auth_headers)
    res = client.get("/api/ledger/", headers=admin_auth_headers)
    entries = res.json()
    assert len(entries) == 2
    assert entries[0]["description"] == "Second"
    assert entries[1]["description"] == "First"


def test_filter_by_event_type(client, campaign, admin_auth_headers):
    client.post("/api/ledger/", json={"event_type": "AdminAdjustment", "description": "Adjust"}, headers=admin_auth_headers)
    client.post("/api/ledger/", json={"event_type": "Purchase", "description": "Buy"}, headers=admin_auth_headers)

    res = client.get("/api/ledger/?event_type=Purchase", headers=admin_auth_headers)
    entries = res.json()
    assert all(e["event_type"] == "Purchase" for e in entries)
    assert len(entries) == 1


def test_ledger_scoped_to_campaign(client, db_session, campaign, admin_auth_headers):
    from conftest import _create_user_with_token
    from app.modules.campaigns import models as campaign_models

    other_camp = campaign_models.Campaign(name="Other Camp", discord_guild_id="999")
    db_session.add(other_camp)
    db_session.commit()
    db_session.refresh(other_camp)
    _, other_token = _create_user_with_token(db_session, "other_led", "OtherLed", "admin", other_camp.id)
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # Post entry in original campaign
    client.post("/api/ledger/", json={"event_type": "AdminAdjustment", "description": "Campaign 1 entry"}, headers=admin_auth_headers)

    # Other campaign sees empty ledger
    res = client.get("/api/ledger/", headers=other_headers)
    assert res.status_code == 200
    assert res.json() == []


def test_ship_adjust_auto_creates_ledger_entry(client, campaign, admin_auth_headers):
    """Adjusting ship essence automatically creates a ledger entry."""
    client.post(
        "/api/ship/adjust",
        json={"essence_delta": 15, "description": "Exploration run"},
        headers=admin_auth_headers,
    )
    res = client.get("/api/ledger/", headers=admin_auth_headers)
    entries = res.json()
    assert len(entries) == 1
    entry = entries[0]
    assert entry["essence_delta"] == 15
    assert entry["ship_snapshot"]["essence"] is not None


def test_ledger_snapshot_reflects_post_adjustment_state(client, campaign, admin_auth_headers):
    """Snapshot in the ledger entry should reflect the ship state after the adjustment."""
    client.put("/api/ship/", json={"essence": 10}, headers=admin_auth_headers)
    client.post(
        "/api/ship/adjust",
        json={"essence_delta": 26, "description": "Big mission"},
        headers=admin_auth_headers,
    )
    entries = client.get("/api/ledger/", headers=admin_auth_headers).json()
    snapshot = entries[0]["ship_snapshot"]
    assert snapshot["essence"] == 36
    assert snapshot["level"] == 6  # 36 >= threshold for level 6


def test_ledger_limit_and_offset(client, campaign, admin_auth_headers):
    for i in range(5):
        client.post("/api/ledger/", json={"event_type": "AdminAdjustment", "description": f"Entry {i}"}, headers=admin_auth_headers)

    res = client.get("/api/ledger/?limit=3", headers=admin_auth_headers)
    assert len(res.json()) == 3

    res2 = client.get("/api/ledger/?limit=3&offset=3", headers=admin_auth_headers)
    assert len(res2.json()) == 2
