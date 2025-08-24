import pytest
from fastapi.testclient import TestClient

# The 'client' fixture is provided by conftest.py and sets up the app and DB.

def test_create_user_success(client: TestClient):
    """Test successful user creation and default character assignment."""
    response = client.post(
        "/api/users/",
        json={"username": "testuser", "email": "test@example.com", "password": "password123"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "hashed_password" not in data
    assert len(data["characters"]) == 1
    assert data["characters"][0]["name"] == "testuser's Character"

def test_create_user_duplicate_username(client: TestClient):
    """Test that creating a user with an existing username fails."""
    client.post("/api/users/", json={"username": "testuser", "email": "test1@example.com", "password": "password123"})
    response = client.post(
        "/api/users/",
        json={"username": "testuser", "email": "test2@example.com", "password": "password123"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Username already registered"}

def test_create_user_duplicate_email(client: TestClient):
    """Test that creating a user with an existing email fails."""
    client.post("/api/users/", json={"username": "testuser1", "email": "test@example.com", "password": "password123"})
    response = client.post(
        "/api/users/",
        json={"username": "testuser2", "email": "test@example.com", "password": "password123"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Email already registered"}

def test_login_for_access_token(client: TestClient):
    """Test successful login and token generation."""
    client.post("/api/users/", json={"username": "loginuser", "email": "login@example.com", "password": "password123"})
    response = client.post(
        "/api/token",
        data={"username": "loginuser", "password": "password123"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_incorrect_password(client: TestClient):
    """Test login with an incorrect password."""
    client.post("/api/users/", json={"username": "loginuser", "email": "login@example.com", "password": "password123"})
    response = client.post(
        "/api/token",
        data={"username": "loginuser", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}

def test_read_users_me_success(client: TestClient):
    """Test fetching the current user's data with a valid token."""
    client.post("/api/users/", json={"username": "me_user", "email": "me@example.com", "password": "password123"})
    login_response = client.post("/api/token", data={"username": "me_user", "password": "password123"})
    token = login_response.json()["access_token"]

    me_response = client.get(
        "/api/users/me/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200, me_response.text
    data = me_response.json()
    assert data["username"] == "me_user"
    assert data["email"] == "me@example.com"

def test_read_users_me_invalid_token(client: TestClient):
    """Test that fetching user data with an invalid token fails."""
    response = client.get(
        "/api/users/me/",
        headers={"Authorization": "Bearer invalidtoken"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}
