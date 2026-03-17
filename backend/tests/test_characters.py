import pytest
from conftest import _create_user_with_token
from app.modules.auth import models as auth_models
from app import security


def test_create_character(client, campaign, player_auth_headers):
    res = client.post("/api/characters/", json={"name": "New Hero"}, headers=player_auth_headers)
    assert res.status_code == 200
    assert res.json()["name"] == "New Hero"


def test_create_character_auto_sets_active_if_none(client, db_session, campaign):
    user = auth_models.User(
        username="NoCharUser", discord_id="no_char_456",
        campaign_id=campaign.id, role="player",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    token = security.create_access_token(
        data={"sub": "no_char_456", "campaign_id": campaign.id, "role": "player"}
    )
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post("/api/characters/", json={"name": "First Hero"}, headers=headers)
    assert res.status_code == 200

    db_session.refresh(user)
    assert user.active_character_id == res.json()["id"]


def test_list_my_characters(client, campaign, player_auth_headers):
    client.post("/api/characters/", json={"name": "Alt Hero"}, headers=player_auth_headers)
    res = client.get("/api/characters/", headers=player_auth_headers)
    assert res.status_code == 200
    names = [c["name"] for c in res.json()]
    assert "Alt Hero" in names


def test_list_characters_excludes_other_users(client, db_session, campaign, player_auth_headers):
    _, other_token = _create_user_with_token(db_session, "other_list", "OtherList", "player", campaign.id)
    other_headers = {"Authorization": f"Bearer {other_token}"}
    client.post("/api/characters/", json={"name": "Other Hero"}, headers=other_headers)

    res = client.get("/api/characters/", headers=player_auth_headers)
    assert res.status_code == 200
    names = [c["name"] for c in res.json()]
    assert "Other Hero" not in names


def test_get_character(client, campaign, player_auth_headers):
    me = client.get("/api/auth/me", headers=player_auth_headers).json()
    char_id = me["characters"][0]["id"]
    res = client.get(f"/api/characters/{char_id}", headers=player_auth_headers)
    assert res.status_code == 200
    assert res.json()["id"] == char_id


def test_get_character_not_found(client, campaign, player_auth_headers):
    res = client.get("/api/characters/99999", headers=player_auth_headers)
    assert res.status_code == 404


def test_update_character_owner(client, campaign, player_auth_headers):
    me = client.get("/api/auth/me", headers=player_auth_headers).json()
    char_id = me["characters"][0]["id"]
    res = client.put(
        f"/api/characters/{char_id}",
        json={"name": "Renamed Hero"},
        headers=player_auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["name"] == "Renamed Hero"


def test_update_character_other_user_forbidden(client, db_session, campaign, player_auth_headers):
    _, other_token = _create_user_with_token(db_session, "other_upd", "OtherUpd", "player", campaign.id)
    other_headers = {"Authorization": f"Bearer {other_token}"}
    me = client.get("/api/auth/me", headers=player_auth_headers).json()
    char_id = me["characters"][0]["id"]

    res = client.put(f"/api/characters/{char_id}", json={"name": "Stolen"}, headers=other_headers)
    assert res.status_code == 403


def test_admin_can_update_any_character(client, campaign, player_auth_headers, admin_auth_headers):
    me = client.get("/api/auth/me", headers=player_auth_headers).json()
    char_id = me["characters"][0]["id"]
    res = client.put(
        f"/api/characters/{char_id}",
        json={"name": "Admin Renamed"},
        headers=admin_auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["name"] == "Admin Renamed"


def test_activate_character(client, campaign, player_auth_headers):
    second = client.post("/api/characters/", json={"name": "Second Hero"}, headers=player_auth_headers).json()
    res = client.post(f"/api/characters/{second['id']}/activate", headers=player_auth_headers)
    assert res.status_code == 200
    assert res.json()["active_character"]["id"] == second["id"]


def test_activate_character_not_owned(client, db_session, campaign, player_auth_headers):
    _, other_token = _create_user_with_token(db_session, "other_act", "OtherAct", "player", campaign.id)
    other_headers = {"Authorization": f"Bearer {other_token}"}
    me = client.get("/api/auth/me", headers=player_auth_headers).json()
    char_id = me["characters"][0]["id"]

    res = client.post(f"/api/characters/{char_id}/activate", headers=other_headers)
    assert res.status_code == 404


def test_delete_character(client, campaign, player_auth_headers):
    doomed = client.post("/api/characters/", json={"name": "Doomed"}, headers=player_auth_headers).json()
    res = client.delete(f"/api/characters/{doomed['id']}", headers=player_auth_headers)
    assert res.status_code == 204


def test_delete_character_not_owner_forbidden(client, db_session, campaign, player_auth_headers):
    _, other_token = _create_user_with_token(db_session, "other_del", "OtherDel", "player", campaign.id)
    other_headers = {"Authorization": f"Bearer {other_token}"}
    me = client.get("/api/auth/me", headers=player_auth_headers).json()
    char_id = me["characters"][0]["id"]
    res = client.delete(f"/api/characters/{char_id}", headers=other_headers)
    assert res.status_code == 403


def test_delete_active_character_clears_active_id(client, db_session, campaign):
    user, token = _create_user_with_token(db_session, "del_active", "DelActive", "player", campaign.id)
    headers = {"Authorization": f"Bearer {token}"}
    char_id = user.active_character_id
    client.delete(f"/api/characters/{char_id}", headers=headers)
    db_session.refresh(user)
    assert user.active_character_id is None
