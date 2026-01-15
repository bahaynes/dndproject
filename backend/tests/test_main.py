import pytest
from app.modules.characters import models as char_models
from app.modules.campaigns import models as campaign_models
from app.modules.auth import models as auth_models
from datetime import datetime
from app.database import Base, get_db
from app.config import get_settings
from app import security

# --- Helpers ---
@pytest.fixture
def campaign(db_session):
    pass

def create_auth_headers(client, db_session, username, discord_id, role, campaign_id):
    # 1. Create User in DB
    user = auth_models.User(
        username=username,
        discord_id=discord_id,
        campaign_id=campaign_id,
        role=role
    )
    db_session.add(user)

    # Create Character
    char = char_models.Character(name=f"{username}'s Character", owner=user, campaign_id=campaign_id)
    db_session.add(char)
    char_stats = char_models.CharacterStats(character=char)
    db_session.add(char_stats)
    
    # Set as active character
    db_session.flush() # Ensure char has ID
    user.active_character_id = char.id
    db_session.add(user)

    db_session.commit()
    db_session.refresh(user)

    # 2. Generate Token
    access_token = security.create_access_token(data={
        "sub": discord_id,
        "campaign_id": campaign_id,
        "role": role
    })

    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def setup_data(db_session):
    # Create Campaign
    camp = campaign_models.Campaign(
        name="Test Campaign",
        discord_guild_id="1234567890",
        dm_role_id="dm",
        player_role_id="player"
    )
    db_session.add(camp)
    db_session.commit()
    db_session.refresh(camp)
    return camp

# --- Test Cases ---

def test_read_users_me_success(client, db_session, setup_data):
    headers = create_auth_headers(client, db_session, "me_user", "u_me", "player", setup_data.id)

    # Correct URL: /api/auth/me
    me_response = client.get(
        "/api/auth/me",
        headers=headers,
    )
    assert me_response.status_code == 200
    data = me_response.json()
    assert data["username"] == "me_user"
    assert data["campaign_id"] == setup_data.id

def test_read_users_me_invalid_token(client):
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalidtoken"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

def test_read_character_success(client, db_session, setup_data):
    headers = create_auth_headers(client, db_session, "char_owner", "u_char", "player", setup_data.id)

    # Get user to get character id
    me_response = client.get("/api/auth/me", headers=headers)
    assert me_response.status_code == 200
    user_data = me_response.json()
    character_id = user_data["characters"][0]["id"]

    # Read the character
    char_response = client.get(f"/api/characters/{character_id}", headers=headers)
    assert char_response.status_code == 200
    char_data = char_response.json()
    assert char_data["id"] == character_id
    assert char_data["name"] == "char_owner's Character"

def test_update_character_success(client, db_session, setup_data):
    headers = create_auth_headers(client, db_session, "update_char", "u_upd", "player", setup_data.id)

    # Get character ID
    me_response = client.get("/api/auth/me", headers=headers)
    character_id = me_response.json()["characters"][0]["id"]

    # Update the character
    update_data = {"name": "Updated Name", "description": "Updated Description"}
    update_response = client.put(
        f"/api/characters/{character_id}",
        headers=headers,
        json=update_data,
    )
    assert update_response.status_code == 200
    updated_char_data = update_response.json()
    assert updated_char_data["name"] == "Updated Name"
    assert updated_char_data["description"] == "Updated Description"

def test_item_endpoints(client, db_session, setup_data):
    headers = create_auth_headers(client, db_session, "item_admin", "u_item", "admin", setup_data.id)

    # Test create_item
    response = client.post("/api/items/", json={"name": "Test Item", "description": "A test item"}, headers=headers)
    assert response.status_code == 200
    item_id = response.json()["id"]
    assert response.json()["name"] == "Test Item"

    # Test read_item
    response = client.get(f"/api/items/{item_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Test Item"

    # Test read_items
    response = client.get("/api/items/", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_inventory_endpoints(client, db_session, setup_data):
    admin_headers = create_auth_headers(client, db_session, "inv_admin", "u_inv_admin", "admin", setup_data.id)
    player_headers = create_auth_headers(client, db_session, "inv_player", "u_inv_player", "player", setup_data.id)

    # Get character ID for player
    me_response = client.get("/api/auth/me", headers=player_headers)
    character_id = me_response.json()["characters"][0]["id"]

    # Create an item (as admin)
    item_response = client.post("/api/items/", json={"name": "Inv Item", "description": "An inventory item"}, headers=admin_headers)
    item_id = item_response.json()["id"]

    # Add item to inventory (admin)
    response = client.post(f"/api/characters/{character_id}/inventory?item_id={item_id}&quantity=5", headers=admin_headers)
    assert response.status_code == 200
    inventory_item_id = response.json()["id"]
    assert response.json()["quantity"] == 5

    # Remove item from inventory
    response = client.delete(f"/api/characters/{character_id}/inventory/{inventory_item_id}?quantity=2", headers=player_headers)
    assert response.status_code == 200
    assert response.json()["quantity"] == 3

def test_store_endpoints(client, db_session, setup_data):
    admin_headers = create_auth_headers(client, db_session, "store_admin", "u_store_admin", "admin", setup_data.id)
    player_headers = create_auth_headers(client, db_session, "store_buyer", "u_store_buyer", "player", setup_data.id)

    # Create an item
    item_res = client.post("/api/items/", json={"name": "Store Item", "description": "A store item"}, headers=admin_headers)
    item_id = item_res.json()["id"]

    # Create a store item
    store_item_res = client.post("/api/store/items/", json={"item_id": item_id, "price": 100, "quantity_available": 10}, headers=admin_headers)
    assert store_item_res.status_code == 200
    store_item_id = store_item_res.json()["id"]

    # Read store items
    res = client.get("/api/store/items/", headers=player_headers)
    assert res.status_code == 200
    assert len(res.json()) > 0

    # Purchase item
    me_res = client.get("/api/auth/me", headers=player_headers)
    char_id = me_res.json()["characters"][0]["id"]

    # Give scrip
    character = db_session.query(char_models.Character).filter(char_models.Character.id == char_id).first()
    character.stats.scrip = 500
    db_session.commit()

    res = client.post(f"/api/store/items/{store_item_id}/purchase?quantity=3", headers=player_headers)
    assert res.status_code == 200
    assert res.json()["message"] == "Purchase successful"

def test_mission_endpoints(client, db_session, setup_data):
    admin_headers = create_auth_headers(client, db_session, "mission_admin", "u_miss_admin", "admin", setup_data.id)
    player_headers = create_auth_headers(client, db_session, "mission_player", "u_miss_player", "player", setup_data.id)

    # Create mission
    mission_res = client.post("/api/missions/", json={"name": "Test Mission", "description": "A test mission", "status": "Active", "rewards": []}, headers=admin_headers)
    assert mission_res.status_code == 200
    mission_id = mission_res.json()["id"]

    # Read missions
    res = client.get("/api/missions/", headers=player_headers)
    assert res.status_code == 200
    assert len(res.json()) > 0

    # Read mission
    res = client.get(f"/api/missions/{mission_id}", headers=player_headers)
    assert res.status_code == 200
    assert res.json()["name"] == "Test Mission"

    # Sign up for mission
    res = client.post(f"/api/missions/{mission_id}/signup", headers=player_headers)
    assert res.status_code == 200
    assert len(res.json()["players"]) == 1

    # Update mission status
    res = client.put(f"/api/missions/{mission_id}/status?status=Completed", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "Completed"

    # Distribute rewards
    res = client.post(f"/api/missions/{mission_id}/distribute_rewards", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["message"] == "Rewards distributed successfully"

def test_game_session_endpoints(client, db_session, setup_data):
    admin_headers = create_auth_headers(client, db_session, "session_admin", "u_sess_admin", "admin", setup_data.id)
    player_headers = create_auth_headers(client, db_session, "session_player", "u_sess_player", "player", setup_data.id)

    # Create session
    session_res = client.post("/api/sessions/", json={"name": "Test Session", "description": "A test session", "status": "Open", "session_date": datetime.now().isoformat()}, headers=admin_headers)
    assert session_res.status_code == 200
    session_id = session_res.json()["id"]

    # Read sessions
    res = client.get("/api/sessions/", headers=player_headers)
    assert res.status_code == 200
    assert len(res.json()) > 0

    # Read session
    res = client.get(f"/api/sessions/{session_id}", headers=player_headers)
    assert res.status_code == 200
    assert res.json()["name"] == "Test Session"

    # Sign up for session
    res = client.post(f"/api/sessions/{session_id}/signup", headers=player_headers)
    assert res.status_code == 200
    assert len(res.json()["players"]) == 1

    # Cancel signup
    res = client.delete(f"/api/sessions/{session_id}/signup", headers=player_headers)
    assert res.status_code == 200
    assert len(res.json()["players"]) == 0

    # Update session
    update_data = {
        "name": "New Session Name",
        "description": "New description",
        "status": "Completed",
        "session_date": datetime.now().isoformat(),
        "after_action_report": "The session was a success!"
    }
    res = client.put(f"/api/sessions/{session_id}", json=update_data, headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "New Session Name"
    assert data["status"] == "Completed"
    assert data["after_action_report"] == "The session was a success!"
