import pytest
from datetime import datetime

SESSION_DATE = datetime(2026, 6, 1, 18, 0).isoformat()


@pytest.fixture
def session_and_mission(client, campaign, admin_auth_headers):
    """Creates a session (min_players=1) and a mission. Returns (session_id, mission_id)."""
    miss = client.post(
        "/api/missions/",
        json={"name": "Test Mission", "description": "A mission", "status": "Available", "rewards": []},
        headers=admin_auth_headers,
    ).json()
    sess = client.post(
        "/api/sessions/",
        json={"name": "Test Session", "session_date": SESSION_DATE, "min_players": 1},
        headers=admin_auth_headers,
    ).json()
    return sess["id"], miss["id"]


# --- Session-First Proposals ---

def test_propose_requires_signup(client, campaign, player_auth_headers, session_and_mission):
    session_id, mission_id = session_and_mission
    res = client.post(
        "/api/sessions/proposals",
        json={"session_id": session_id, "mission_id": mission_id},
        headers=player_auth_headers,
    )
    assert res.status_code == 403


def test_propose_mission_after_signup(client, campaign, player_auth_headers, session_and_mission):
    session_id, mission_id = session_and_mission
    client.post(f"/api/sessions/{session_id}/signup", headers=player_auth_headers)
    res = client.post(
        "/api/sessions/proposals",
        json={"session_id": session_id, "mission_id": mission_id},
        headers=player_auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["session_id"] == session_id
    assert res.json()["mission_id"] == mission_id
    assert res.json()["status"] == "proposed"


def test_propose_hex_after_signup(client, campaign, admin_auth_headers, player_auth_headers, session_and_mission):
    session_id, _ = session_and_mission
    # Create a map & discovered hex
    hmap = client.post(
        "/api/maps/",
        json={"name": "Frontier", "width": 5, "height": 5},
        headers=admin_auth_headers,
    ).json()
    first_hex = hmap["hexes"][0]
    hex_id = first_hex["id"]
    client.put(
        f"/api/maps/{hmap['id']}/hexes/{first_hex['q']}/{first_hex['r']}",
        json={"is_discovered": True, "linked_location_name": "Sunken Spire"},
        headers=admin_auth_headers,
    )

    client.post(f"/api/sessions/{session_id}/signup", headers=player_auth_headers)
    res = client.post(
        "/api/sessions/proposals",
        json={"session_id": session_id, "hex_id": hex_id},
        headers=player_auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["hex_id"] == hex_id
    assert res.json()["hex"]["linked_location_name"] == "Sunken Spire"


# --- Advisory Consensus Voting ---

def test_toggle_back_adds_and_removes_without_auto_confirm(client, campaign, player_auth_headers, session_and_mission):
    session_id, mission_id = session_and_mission
    client.post(f"/api/sessions/{session_id}/signup", headers=player_auth_headers)
    proposal = client.post(
        "/api/sessions/proposals",
        json={"session_id": session_id, "mission_id": mission_id},
        headers=player_auth_headers,
    ).json()
    pid = proposal["id"]

    res = client.post(f"/api/sessions/proposals/{pid}/toggle_back", headers=player_auth_headers)
    assert res.status_code == 200
    assert len(res.json()["backers"]) == 1

    # Advisory only: even with min_players=1, session stays Scheduled
    session = client.get(f"/api/sessions/{session_id}", headers=player_auth_headers).json()
    assert session["status"] == "Scheduled"

    res2 = client.post(f"/api/sessions/proposals/{pid}/toggle_back", headers=player_auth_headers)
    assert res2.status_code == 200
    assert len(res2.json()["backers"]) == 0


def test_voting_switches_cleanly_between_proposals(client, campaign, admin_auth_headers, player_auth_headers):
    miss1 = client.post("/api/missions/", json={"name": "Mission A", "description": "d", "status": "Available", "rewards": []}, headers=admin_auth_headers).json()
    miss2 = client.post("/api/missions/", json={"name": "Mission B", "description": "d", "status": "Available", "rewards": []}, headers=admin_auth_headers).json()
    sess = client.post("/api/sessions/", json={"name": "Poll", "session_date": SESSION_DATE, "min_players": 4}, headers=admin_auth_headers).json()

    client.post(f"/api/sessions/{sess['id']}/signup", headers=player_auth_headers)
    prop1 = client.post("/api/sessions/proposals", json={"session_id": sess["id"], "mission_id": miss1["id"]}, headers=player_auth_headers).json()
    prop2 = client.post("/api/sessions/proposals", json={"session_id": sess["id"], "mission_id": miss2["id"]}, headers=player_auth_headers).json()

    client.post(f"/api/sessions/proposals/{prop1['id']}/toggle_back", headers=player_auth_headers)
    res = client.post(f"/api/sessions/proposals/{prop2['id']}/toggle_back", headers=player_auth_headers)
    assert res.status_code == 200
    assert len(res.json()["backers"]) == 1

    # Vote moved off prop1
    updated_sess = client.get(f"/api/sessions/{sess['id']}", headers=player_auth_headers).json()
    p1 = next(p for p in updated_sess["proposals"] if p["id"] == prop1["id"])
    assert len(p1["backers"]) == 0


# --- Swap Character ---

def test_swap_character_in_session(client, campaign, player_auth_headers, session_and_mission):
    session_id, mission_id = session_and_mission
    alt = client.post("/api/characters/", json={"name": "Alt Wizard", "class_name": "Wizard"}, headers=player_auth_headers).json()

    client.post(f"/api/sessions/{session_id}/signup", headers=player_auth_headers)
    proposal = client.post("/api/sessions/proposals", json={"session_id": session_id, "mission_id": mission_id}, headers=player_auth_headers).json()
    client.post(f"/api/sessions/proposals/{proposal['id']}/toggle_back", headers=player_auth_headers)

    res = client.post(
        f"/api/sessions/{session_id}/swap-character",
        json={"character_id": alt["id"]},
        headers=player_auth_headers,
    )
    assert res.status_code == 200
    player_ids = [p["id"] for p in res.json()["players"]]
    assert player_ids == [alt["id"]]
    assert [b["id"] for b in res.json()["proposals"][0]["backers"]] == [alt["id"]]


# --- Admin Lock & Night-Of Completion ---

def test_force_confirm_keeps_existing_players(client, campaign, admin_auth_headers, player_auth_headers, session_and_mission):
    session_id, mission_id = session_and_mission
    client.post(f"/api/sessions/{session_id}/signup", headers=player_auth_headers)
    proposal = client.post(
        "/api/sessions/proposals",
        json={"session_id": session_id, "mission_id": mission_id},
        headers=player_auth_headers,
    ).json()
    res = client.post(f"/api/sessions/proposals/{proposal['id']}/force_confirm", headers=admin_auth_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "Confirmed"
    assert len(res.json()["players"]) == 1


def test_complete_session_night_of_mission(client, campaign, admin_auth_headers, player_auth_headers, session_and_mission):
    session_id, mission_id = session_and_mission
    client.post(f"/api/sessions/{session_id}/signup", headers=player_auth_headers)
    res = client.post(
        f"/api/sessions/{session_id}/complete",
        json={"result": "success", "mission_id": mission_id, "gold_earned": 50, "xp_earned": 300},
        headers=admin_auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["status"] == "Completed"
    assert res.json()["confirmed_mission_id"] == mission_id


def test_force_confirm_player_forbidden(client, campaign, player_auth_headers, session_and_mission):
    session_id, mission_id = session_and_mission
    client.post(f"/api/sessions/{session_id}/signup", headers=player_auth_headers)
    proposal = client.post(
        "/api/sessions/proposals",
        json={"session_id": session_id, "mission_id": mission_id},
        headers=player_auth_headers,
    ).json()
    res = client.post(f"/api/sessions/proposals/{proposal['id']}/force_confirm", headers=player_auth_headers)
    assert res.status_code == 403


def test_veto_proposal_admin_and_forbidden(client, campaign, admin_auth_headers, player_auth_headers, session_and_mission):
    session_id, mission_id = session_and_mission
    client.post(f"/api/sessions/{session_id}/signup", headers=player_auth_headers)
    proposal = client.post(
        "/api/sessions/proposals",
        json={"session_id": session_id, "mission_id": mission_id},
        headers=player_auth_headers,
    ).json()
    assert client.post(f"/api/sessions/proposals/{proposal['id']}/veto", headers=player_auth_headers).status_code == 403
    res = client.post(f"/api/sessions/proposals/{proposal['id']}/veto", headers=admin_auth_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "vetoed"


# --- Field reports & Kick ---

def test_field_report_participant_can_submit(client, campaign, admin_auth_headers, player_auth_headers, session_and_mission):
    session_id, _ = session_and_mission
    client.post(f"/api/sessions/{session_id}/signup", headers=player_auth_headers)
    client.put(
        f"/api/sessions/{session_id}",
        json={"name": "Done Session", "session_date": SESSION_DATE, "status": "Completed"},
        headers=admin_auth_headers,
    )
    res = client.patch(
        f"/api/sessions/{session_id}/field-report",
        json={"field_report": "We won!"},
        headers=player_auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["field_report"] == "We won!"


def test_field_report_non_participant_forbidden(client, campaign, player_auth_headers, session_and_mission):
    session_id, _ = session_and_mission
    res = client.patch(
        f"/api/sessions/{session_id}/field-report",
        json={"field_report": "I wasn't there"},
        headers=player_auth_headers,
    )
    assert res.status_code == 403


def test_kick_player_admin_and_forbidden(client, campaign, admin_auth_headers, player_auth_headers, session_and_mission):
    session_id, _ = session_and_mission
    client.post(f"/api/sessions/{session_id}/signup", headers=player_auth_headers)
    me = client.get("/api/auth/me", headers=player_auth_headers).json()
    char_id = me["characters"][0]["id"]

    assert client.delete(f"/api/sessions/{session_id}/kick/{char_id}", headers=player_auth_headers).status_code == 403
    res = client.delete(f"/api/sessions/{session_id}/kick/{char_id}", headers=admin_auth_headers)
    assert res.status_code == 200
    assert char_id not in [p["id"] for p in res.json()["players"]]
