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
    assert len(data["characters"]) == 1
    assert data["characters"][0]["name"] == "testuser's Character"


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
