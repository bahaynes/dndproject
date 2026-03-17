import pytest
from conftest import _create_user_with_token
from app.modules.campaigns import models as campaign_models


def _create_map(client, admin_headers, name="Test Map", seed=True):
    res = client.post(
        "/api/maps/",
        json={"name": name, "width": 5, "height": 5, "hex_size": 60},
        headers=admin_headers,
    )
    assert res.status_code == 200
    return res.json()


def test_get_maps_lazy_creates_default(client, campaign, player_auth_headers):
    res = client.get("/api/maps/", headers=player_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["name"] == "The Known World"


def test_get_maps_returns_existing(client, campaign, player_auth_headers, admin_auth_headers):
    _create_map(client, admin_auth_headers, name="My Map")
    res = client.get("/api/maps/", headers=player_auth_headers)
    assert res.status_code == 200
    assert any(m["name"] == "My Map" for m in res.json())


def test_create_map_admin(client, campaign, admin_auth_headers):
    res = client.post(
        "/api/maps/",
        json={"name": "Admin Map", "width": 10, "height": 10, "hex_size": 60},
        headers=admin_auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["name"] == "Admin Map"


def test_create_map_player_forbidden(client, campaign, player_auth_headers):
    res = client.post(
        "/api/maps/",
        json={"name": "Player Map", "width": 10, "height": 10, "hex_size": 60},
        headers=player_auth_headers,
    )
    assert res.status_code == 403


def test_get_map_by_id(client, campaign, player_auth_headers, admin_auth_headers):
    m = _create_map(client, admin_auth_headers)
    res = client.get(f"/api/maps/{m['id']}", headers=player_auth_headers)
    assert res.status_code == 200
    assert res.json()["id"] == m["id"]


def test_get_map_not_found(client, campaign, player_auth_headers):
    res = client.get("/api/maps/99999", headers=player_auth_headers)
    assert res.status_code == 404


def test_get_map_other_campaign_returns_404(client, db_session, campaign, player_auth_headers):
    other_camp = campaign_models.Campaign(name="Other Camp", discord_guild_id="999")
    db_session.add(other_camp)
    db_session.commit()
    db_session.refresh(other_camp)
    _, other_token = _create_user_with_token(db_session, "other_map", "OtherMap", "admin", other_camp.id)
    other_headers = {"Authorization": f"Bearer {other_token}"}
    other_map = client.post(
        "/api/maps/",
        json={"name": "Other Map", "width": 5, "height": 5, "hex_size": 60},
        headers=other_headers,
    ).json()

    res = client.get(f"/api/maps/{other_map['id']}", headers=player_auth_headers)
    assert res.status_code == 404


def test_update_hex_admin(client, campaign, admin_auth_headers):
    m = _create_map(client, admin_auth_headers)
    res = client.put(
        f"/api/maps/{m['id']}/hexes/0/0",
        json={"is_discovered": True, "hex_state": "friendly"},
        headers=admin_auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["is_discovered"] is True
    assert res.json()["hex_state"] == "friendly"


def test_update_hex_player_forbidden(client, campaign, admin_auth_headers, player_auth_headers):
    m = _create_map(client, admin_auth_headers)
    res = client.put(
        f"/api/maps/{m['id']}/hexes/0/0",
        json={"is_discovered": True},
        headers=player_auth_headers,
    )
    assert res.status_code == 403


def test_add_player_note_on_discovered_hex(client, campaign, player_auth_headers):
    # Lazy-created map seeds q=0,r=0 as discovered
    maps = client.get("/api/maps/", headers=player_auth_headers).json()
    map_id = maps[0]["id"]
    res = client.post(
        f"/api/maps/{map_id}/hexes/0/0/notes",
        json={"text": "There's a cave here"},
        headers=player_auth_headers,
    )
    assert res.status_code == 200
    assert any(n["text"] == "There's a cave here" for n in res.json()["player_notes"])


def test_add_player_note_on_undiscovered_hex(client, campaign, player_auth_headers):
    # q=1,r=0 exists in the seeded grid (radius=5) but is_discovered=False
    maps = client.get("/api/maps/", headers=player_auth_headers).json()
    map_id = maps[0]["id"]
    res = client.post(
        f"/api/maps/{map_id}/hexes/1/0/notes",
        json={"text": "Secret note"},
        headers=player_auth_headers,
    )
    assert res.status_code == 400
    assert "undiscovered" in res.json()["detail"].lower()


def test_add_note_wrong_campaign(client, db_session, campaign, player_auth_headers):
    other_camp = campaign_models.Campaign(name="Other Camp 2", discord_guild_id="888")
    db_session.add(other_camp)
    db_session.commit()
    db_session.refresh(other_camp)
    _, other_token = _create_user_with_token(db_session, "note_other", "NoteOther", "admin", other_camp.id)
    other_headers = {"Authorization": f"Bearer {other_token}"}
    other_map = client.post(
        "/api/maps/",
        json={"name": "Other Map", "width": 5, "height": 5, "hex_size": 60},
        headers=other_headers,
    ).json()

    res = client.post(
        f"/api/maps/{other_map['id']}/hexes/0/0/notes",
        json={"text": "Cross-campaign note"},
        headers=player_auth_headers,
    )
    assert res.status_code == 404
