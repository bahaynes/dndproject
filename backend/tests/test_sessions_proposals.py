import pytest
from datetime import datetime
from conftest import _create_user_with_token

SESSION_DATE = datetime(2026, 6, 1, 18, 0).isoformat()


@pytest.fixture
def session_and_mission(client, campaign, admin_auth_headers):
    """Creates a session (min_players=1) and a mission. Returns (session_id, mission_id)."""
    miss = client.post(
        "/api/missions/",
        json={"name": "Test Mission", "description": "A mission", "status": "Active", "rewards": []},
        headers=admin_auth_headers,
    ).json()
    sess = client.post(
        "/api/sessions/",
        json={"name": "Test Session", "session_date": SESSION_DATE, "min_players": 1},
        headers=admin_auth_headers,
    ).json()
    return sess["id"], miss["id"]


# --- Proposals ---

def test_propose_mission(client, campaign, admin_auth_headers, player_auth_headers, session_and_mission):
    session_id, mission_id = session_and_mission
    res = client.post(
        "/api/sessions/proposals",
        json={"session_id": session_id, "mission_id": mission_id},
        headers=player_auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["session_id"] == session_id
    assert res.json()["mission_id"] == mission_id
    assert res.json()["status"] == "proposed"


def test_propose_for_confirmed_session_rejected(client, campaign, admin_auth_headers, player_auth_headers, session_and_mission):
    session_id, mission_id = session_and_mission
    proposal = client.post(
        "/api/sessions/proposals",
        json={"session_id": session_id, "mission_id": mission_id},
        headers=player_auth_headers,
    ).json()
    client.post(f"/api/sessions/proposals/{proposal['id']}/force_confirm", headers=admin_auth_headers)

    res = client.post(
        "/api/sessions/proposals",
        json={"session_id": session_id, "mission_id": mission_id},
        headers=player_auth_headers,
    )
    assert res.status_code == 400
    assert "confirmed" in res.json()["detail"].lower()


# --- Toggle backing ---

def test_toggle_back_adds_backer(client, campaign, admin_auth_headers, player_auth_headers, session_and_mission):
    session_id, mission_id = session_and_mission
    proposal = client.post(
        "/api/sessions/proposals",
        json={"session_id": session_id, "mission_id": mission_id},
        headers=player_auth_headers,
    ).json()
    res = client.post(f"/api/sessions/proposals/{proposal['id']}/toggle_back", headers=player_auth_headers)
    assert res.status_code == 200
    assert len(res.json()["backers"]) == 1


def test_toggle_back_removes_on_second_call(client, campaign, admin_auth_headers, player_auth_headers):
    # Use min_players=4 so a single back doesn't auto-confirm the session
    miss = client.post(
        "/api/missions/",
        json={"name": "Toggle Mission", "description": "d", "status": "Active", "rewards": []},
        headers=admin_auth_headers,
    ).json()
    sess = client.post(
        "/api/sessions/",
        json={"name": "Toggle Session", "session_date": SESSION_DATE, "min_players": 4},
        headers=admin_auth_headers,
    ).json()
    proposal = client.post(
        "/api/sessions/proposals",
        json={"session_id": sess["id"], "mission_id": miss["id"]},
        headers=player_auth_headers,
    ).json()
    pid = proposal["id"]
    client.post(f"/api/sessions/proposals/{pid}/toggle_back", headers=player_auth_headers)
    res = client.post(f"/api/sessions/proposals/{pid}/toggle_back", headers=player_auth_headers)
    assert res.status_code == 200
    assert len(res.json()["backers"]) == 0


def test_toggle_back_auto_confirms_at_min_players(client, campaign, admin_auth_headers, player_auth_headers, session_and_mission):
    """Session with min_players=1 confirms as soon as one backer is added."""
    session_id, mission_id = session_and_mission
    proposal = client.post(
        "/api/sessions/proposals",
        json={"session_id": session_id, "mission_id": mission_id},
        headers=player_auth_headers,
    ).json()
    client.post(f"/api/sessions/proposals/{proposal['id']}/toggle_back", headers=player_auth_headers)
    session = client.get(f"/api/sessions/{session_id}", headers=player_auth_headers).json()
    assert session["status"] == "Confirmed"


def test_cannot_back_two_proposals_in_same_session(client, campaign, admin_auth_headers, player_auth_headers):
    # min_players=4 so a single back doesn't auto-confirm
    miss1 = client.post(
        "/api/missions/",
        json={"name": "Mission A", "description": "d", "status": "Active", "rewards": []},
        headers=admin_auth_headers,
    ).json()
    miss2 = client.post(
        "/api/missions/",
        json={"name": "Mission B", "description": "d", "status": "Active", "rewards": []},
        headers=admin_auth_headers,
    ).json()
    sess = client.post(
        "/api/sessions/",
        json={"name": "Contested", "session_date": SESSION_DATE, "min_players": 4},
        headers=admin_auth_headers,
    ).json()

    prop1 = client.post(
        "/api/sessions/proposals",
        json={"session_id": sess["id"], "mission_id": miss1["id"]},
        headers=player_auth_headers,
    ).json()
    prop2 = client.post(
        "/api/sessions/proposals",
        json={"session_id": sess["id"], "mission_id": miss2["id"]},
        headers=player_auth_headers,
    ).json()

    client.post(f"/api/sessions/proposals/{prop1['id']}/toggle_back", headers=player_auth_headers)
    res = client.post(f"/api/sessions/proposals/{prop2['id']}/toggle_back", headers=player_auth_headers)
    assert res.status_code == 400
    assert "already backed" in res.json()["detail"].lower()


# --- Force confirm ---

def test_force_confirm_proposal_admin(client, campaign, admin_auth_headers, player_auth_headers, session_and_mission):
    session_id, mission_id = session_and_mission
    proposal = client.post(
        "/api/sessions/proposals",
        json={"session_id": session_id, "mission_id": mission_id},
        headers=player_auth_headers,
    ).json()
    res = client.post(f"/api/sessions/proposals/{proposal['id']}/force_confirm", headers=admin_auth_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "Confirmed"


def test_force_confirm_player_forbidden(client, campaign, admin_auth_headers, player_auth_headers, session_and_mission):
    session_id, mission_id = session_and_mission
    proposal = client.post(
        "/api/sessions/proposals",
        json={"session_id": session_id, "mission_id": mission_id},
        headers=player_auth_headers,
    ).json()
    res = client.post(f"/api/sessions/proposals/{proposal['id']}/force_confirm", headers=player_auth_headers)
    assert res.status_code == 403


# --- Veto ---

def test_veto_proposal_admin(client, campaign, admin_auth_headers, player_auth_headers, session_and_mission):
    session_id, mission_id = session_and_mission
    proposal = client.post(
        "/api/sessions/proposals",
        json={"session_id": session_id, "mission_id": mission_id},
        headers=player_auth_headers,
    ).json()
    res = client.post(f"/api/sessions/proposals/{proposal['id']}/veto", headers=admin_auth_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "vetoed"


def test_veto_proposal_player_forbidden(client, campaign, admin_auth_headers, player_auth_headers, session_and_mission):
    session_id, mission_id = session_and_mission
    proposal = client.post(
        "/api/sessions/proposals",
        json={"session_id": session_id, "mission_id": mission_id},
        headers=player_auth_headers,
    ).json()
    res = client.post(f"/api/sessions/proposals/{proposal['id']}/veto", headers=player_auth_headers)
    assert res.status_code == 403


# --- Field reports ---

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


def test_field_report_non_participant_forbidden(client, campaign, admin_auth_headers, player_auth_headers, session_and_mission):
    session_id, _ = session_and_mission
    # Player never signed up
    res = client.patch(
        f"/api/sessions/{session_id}/field-report",
        json={"field_report": "I wasn't there"},
        headers=player_auth_headers,
    )
    assert res.status_code == 403


# --- Kick ---

def test_kick_player_admin(client, campaign, admin_auth_headers, player_auth_headers, session_and_mission):
    session_id, _ = session_and_mission
    client.post(f"/api/sessions/{session_id}/signup", headers=player_auth_headers)
    me = client.get("/api/auth/me", headers=player_auth_headers).json()
    char_id = me["characters"][0]["id"]

    res = client.delete(f"/api/sessions/{session_id}/kick/{char_id}", headers=admin_auth_headers)
    assert res.status_code == 200
    assert char_id not in [p["id"] for p in res.json()["players"]]


def test_kick_player_player_forbidden(client, campaign, admin_auth_headers, player_auth_headers, session_and_mission):
    session_id, _ = session_and_mission
    client.post(f"/api/sessions/{session_id}/signup", headers=player_auth_headers)
    me = client.get("/api/auth/me", headers=player_auth_headers).json()
    char_id = me["characters"][0]["id"]

    res = client.delete(f"/api/sessions/{session_id}/kick/{char_id}", headers=player_auth_headers)
    assert res.status_code == 403
