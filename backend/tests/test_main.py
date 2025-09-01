import pytest

# --- Test Cases ---

def test_create_user_success(client):
    response = client.post(
        "/users/",
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
        "/users/",
        json={"username": "testuser", "email": "test1@example.com", "password": "password123"},
    )
    # Attempt to create a second user with the same username
    response = client.post(
        "/users/",
        json={"username": "testuser", "email": "test2@example.com", "password": "password123"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "This username is already in use. Please choose another one."}

def test_create_user_duplicate_email(client):
    # Create the first user
    client.post(
        "/users/",
        json={"username": "testuser1", "email": "test@example.com", "password": "password123"},
    )
    # Attempt to create a second user with the same email
    response = client.post(
        "/users/",
        json={"username": "testuser2", "email": "test@example.com", "password": "password123"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "This email is already registered. If you have an account, please sign in instead."}


def test_login_for_access_token(client):
    # First, create a user to log in with
    client.post(
        "/users/",
        json={"username": "loginuser", "email": "login@example.com", "password": "password123"},
    )

    # Now, attempt to log in
    response = client.post(
        "/token",
        data={"username": "loginuser", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_incorrect_password(client):
    client.post(
        "/users/",
        json={"username": "loginuser", "email": "login@example.com", "password": "password123"},
    )
    response = client.post(
        "/token",
        data={"username": "loginuser", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}


def test_read_users_me_success(client):
    client.post(
        "/users/",
        json={"username": "me_user", "email": "me@example.com", "password": "password123"},
    )
    login_response = client.post(
        "/token",
        data={"username": "me_user", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    me_response = client.get(
        "/users/me/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    data = me_response.json()
    assert data["username"] == "me_user"
    assert data["email"] == "me@example.com"


def test_read_users_me_invalid_token(client):
    response = client.get(
        "/users/me/",
        headers={"Authorization": "Bearer invalidtoken"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


def test_read_character_success(client):
    # Create a user, which also creates a character
    user_response = client.post(
        "/users/",
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
        "/users/",
        json={"username": "update_char_owner", "email": "update_char@example.com", "password": "password123"},
    )
    login_response = client.post(
        "/token",
        data={"username": "update_char_owner", "password": "password123"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get character ID from the /users/me endpoint
    me_response = client.get("/users/me/", headers=headers)
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
