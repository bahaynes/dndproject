import pytest
from app.modules.characters import models as char_models
from datetime import datetime

# --- Test Cases ---

def test_create_user_success(client):
    response = client.post(
        "/api/users/",
        json={"username": "testuser", "email": "test@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "hashed_password" not in data
    # Check if the default character was created
    assert "character" in data
    assert data["character"] is not None
    assert data["character"]["name"] == "testuser's Character"


def test_create_user_duplicate_username(client):
    # Create the first user
    client.post(
        "/api/users/",
        json={"username": "testuser", "email": "test1@example.com", "password": "password123"},
    )
    # Attempt to create a second user with the same username
    response = client.post(
        "/api/users/",
        json={"username": "testuser", "email": "test2@example.com", "password": "password123"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "This username is already in use. Please choose another one."}

def test_create_user_duplicate_email(client):
    # Create the first user
    client.post(
        "/api/users/",
        json={"username": "testuser1", "email": "test@example.com", "password": "password123"},
    )
    # Attempt to create a second user with the same email
    response = client.post(
        "/api/users/",
        json={"username": "testuser2", "email": "test@example.com", "password": "password123"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "This email is already registered. If you have an account, please sign in instead."}


def test_login_for_access_token(client):
    # First, create a user to log in with
    client.post(
        "/api/users/",
        json={"username": "loginuser", "email": "login@example.com", "password": "password123"},
    )

    # Now, attempt to log in
    response = client.post(
        "/api/token",
        data={"username": "loginuser", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_incorrect_password(client):
    client.post(
        "/api/users/",
        json={"username": "loginuser", "email": "login@example.com", "password": "password123"},
    )
    response = client.post(
        "/api/token",
        data={"username": "loginuser", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}


def test_read_users_me_success(client):
    client.post(
        "/api/users/",
        json={"username": "me_user", "email": "me@example.com", "password": "password123"},
    )
    login_response = client.post(
        "/api/token",
        data={"username": "me_user", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    me_response = client.get(
        "/api/users/me/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    data = me_response.json()
    assert data["username"] == "me_user"
    assert data["email"] == "me@example.com"


def test_read_users_me_invalid_token(client):
    response = client.get(
        "/api/users/me/",
        headers={"Authorization": "Bearer invalidtoken"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


def test_read_character_success(client):
    # Create a user, which also creates a character
    user_response = client.post(
        "/api/users/",
        json={"username": "char_owner", "email": "char@example.com", "password": "password123"},
    )
    assert user_response.status_code == 200
    user_data = user_response.json()
    character_id = user_data["character"]["id"]

    # Read the character
    char_response = client.get(f"/api/characters/{character_id}")
    assert char_response.status_code == 200
    char_data = char_response.json()
    assert char_data["id"] == character_id
    assert char_data["name"] == "char_owner's Character"


def test_update_character_success(client):
    # Create a user and get token
    client.post(
        "/api/users/",
        json={"username": "update_char_owner", "email": "update_char@example.com", "password": "password123"},
    )
    login_response = client.post(
        "/api/token",
        data={"username": "update_char_owner", "password": "password123"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get character ID from the /users/me endpoint
    me_response = client.get("/api/users/me/", headers=headers)
    character_id = me_response.json()["character"]["id"]

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


def test_item_endpoints(client):
    # Create an admin user and get a token
    client.post(
        "/api/users/",
        json={"username": "item_admin", "email": "item_admin@example.com", "password": "password", "role": "admin"},
    )
    response = client.post("/api/token", data={"username": "item_admin", "password": "password"})
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

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


def test_inventory_endpoints(client):
    # Create an admin user for creating items
    client.post(
        "/api/users/",
        json={"username": "inv_admin", "email": "inv_admin@example.com", "password": "password", "role": "admin"},
    )
    admin_login_response = client.post("/api/token", data={"username": "inv_admin", "password": "password"})
    admin_token = admin_login_response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Create a player user
    client.post(
        "/api/users/",
        json={"username": "inv_user", "email": "inv_user@example.com", "password": "password", "role": "player"},
    )
    player_login_response = client.post("/api/token", data={"username": "inv_user", "password": "password"})
    player_token = player_login_response.json()["access_token"]
    player_headers = {"Authorization": f"Bearer {player_token}"}

    # Get character ID
    me_response = client.get("/api/users/me/", headers=player_headers)
    character_id = me_response.json()["character"]["id"]

    # Create an item
    item_response = client.post("/api/items/", json={"name": "Inv Item", "description": "An inventory item"}, headers=admin_headers)
    item_id = item_response.json()["id"]

    # Add item to inventory
    response = client.post(f"/api/characters/{character_id}/inventory?item_id={item_id}&quantity=5", headers=admin_headers)
    assert response.status_code == 200
    inventory_item_id = response.json()["id"]
    assert response.json()["quantity"] == 5

    # Remove item from inventory
    response = client.delete(f"/api/inventory/{inventory_item_id}?quantity=2", headers=player_headers)
    assert response.status_code == 200
    assert response.json()["quantity"] == 3


def test_store_endpoints(client, db_session):
    # Create an admin user and a player user
    client.post("/api/users/", json={"username": "store_admin", "email": "store_admin@example.com", "password": "password", "role": "admin"})
    admin_login = client.post("/api/token", data={"username": "store_admin", "password": "password"})
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    client.post("/api/users/", json={"username": "buyer", "email": "buyer@example.com", "password": "password", "role": "player"})
    player_login = client.post("/api/token", data={"username": "buyer", "password": "password"})
    player_headers = {"Authorization": f"Bearer {player_login.json()['access_token']}"}

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
    me_res = client.get("/api/users/me/", headers=player_headers)
    character = db_session.query(char_models.Character).filter(char_models.Character.id == me_res.json()["character"]["id"]).first()
    character.stats.scrip = 500
    db_session.commit()

    res = client.post(f"/api/store/items/{store_item_id}/purchase?quantity=3", headers=player_headers)
    assert res.status_code == 200
    assert res.json()["message"] == "Purchase successful"


def test_mission_endpoints(client):
    # Create admin and player
    client.post("/api/users/", json={"username": "mission_admin", "email": "mission_admin@example.com", "password": "password", "role": "admin"})
    admin_login = client.post("/api/token", data={"username": "mission_admin", "password": "password"})
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    client.post("/api/users/", json={"username": "mission_player", "email": "mission_player@example.com", "password": "password", "role": "player"})
    player_login = client.post("/api/token", data={"username": "mission_player", "password": "password"})
    player_headers = {"Authorization": f"Bearer {player_login.json()['access_token']}"}

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


def test_game_session_endpoints(client):
    # Create admin and player
    client.post("/api/users/", json={"username": "session_admin", "email": "session_admin@example.com", "password": "password", "role": "admin"})
    admin_login = client.post("/api/token", data={"username": "session_admin", "password": "password"})
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    client.post("/api/users/", json={"username": "session_player", "email": "session_player@example.com", "password": "password", "role": "player"})
    player_login = client.post("/api/token", data={"username": "session_player", "password": "password"})
    player_headers = {"Authorization": f"Bearer {player_login.json()['access_token']}"}

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
