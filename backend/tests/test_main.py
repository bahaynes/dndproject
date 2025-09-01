import pytest
from io import BytesIO

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
    assert response.json() == {"detail": "Username already registered"}

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
    assert response.json() == {"detail": "Email already registered"}


def test_login_for_access_token(client, get_auth_headers):
    # The fixture will create a user "testuser"
    headers = get_auth_headers()
    assert "Authorization" in headers
    assert headers["Authorization"].startswith("Bearer ")

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


def test_read_users_me_success(client, get_auth_headers):
    headers = get_auth_headers("me_user")
    response = client.get(
        "/users/me/",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "me_user"
    assert data["email"] == "me@example.com"


def test_read_users_me_invalid_token(client):
    response = client.get(
        "/users/me/",
        headers={"Authorization": "Bearer invalidtoken"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


def test_read_character_success(client, get_auth_headers):
    headers = get_auth_headers("char_owner")
    me_response = client.get("/users/me/", headers=headers)
    character_id = me_response.json()["character"]["id"]

    # Read the character
    char_response = client.get(f"/api/characters/{character_id}", headers=headers)
    assert char_response.status_code == 200
    char_data = char_response.json()
    assert char_data["id"] == character_id
    assert char_data["name"] == "char_owner's Character"


def test_update_character_success(client, get_auth_headers):
    headers = get_auth_headers("update_char_owner")

    me_response = client.get("/users/me/", headers=headers)
    character_id = me_response.json()["character"]["id"]

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


def test_update_character_partial(client, get_auth_headers):
    headers = get_auth_headers("partial_update_user")

    me_response = client.get("/users/me/", headers=headers)
    character_id = me_response.json()["character"]["id"]
    original_name = me_response.json()["character"]["name"]

    update_data = {"description": "A new partial description"}
    update_response = client.put(
        f"/api/characters/{character_id}",
        headers=headers,
        json=update_data,
    )
    assert update_response.status_code == 200
    updated_char_data = update_response.json()
    assert updated_char_data["name"] == original_name
    assert updated_char_data["description"] == "A new partial description"


def test_upload_character_image(client, get_auth_headers):
    headers = get_auth_headers("image_upload_user")

    me_response = client.get("/users/me/", headers=headers)
    character_id = me_response.json()["character"]["id"]

    # Create a dummy image file
    image_data = BytesIO(b"this is a test image")
    files = {"file": ("test_image.png", image_data, "image/png")}

    upload_response = client.post(
        f"/api/characters/{character_id}/image",
        headers=headers,
        files=files,
    )
    assert upload_response.status_code == 200
    data = upload_response.json()
    assert "image_url" in data
    assert data["image_url"].startswith(f"/static/character_images/{character_id}_")
    assert data["image_url"].endswith(".png")

    # Verify the image URL was updated by fetching the character again
    char_response = client.get(f"/api/characters/{character_id}", headers=headers)
    assert char_response.status_code == 200
    char_data = char_response.json()
    assert char_data["image_url"] == data["image_url"]
