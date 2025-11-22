import pytest
from app.modules.auth.schemas import User
from app.dependencies import get_current_active_user
from app.main import app

def test_map_workflow(client):
    # 1. Admin creates a tile
    app.dependency_overrides[get_current_active_user] = lambda: User(
        id=1, username="admin", email="admin@test.com", role="admin", is_active=True
    )

    response = client.post("/api/map/tiles", json={
        "q": 0, "r": 0, "terrain": "plains", "is_revealed": True, "description": "Start"
    })
    assert response.status_code == 200

    # Create unrevealed tile
    response = client.post("/api/map/tiles", json={
        "q": 1, "r": 0, "terrain": "forest", "is_revealed": False, "description": "Hidden"
    })
    assert response.status_code == 200

    # 2. Admin sees all tiles
    response = client.get("/api/map/tiles")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # 3. Player sees only revealed tiles
    app.dependency_overrides[get_current_active_user] = lambda: User(
        id=2, username="player", email="player@test.com", role="player", is_active=True
    )

    response = client.get("/api/map/tiles")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["q"] == 0
    assert data[0]["r"] == 0

def test_tile_update(client):
    # Admin creates tile
    app.dependency_overrides[get_current_active_user] = lambda: User(
        id=1, username="admin", email="admin@test.com", role="admin", is_active=True
    )

    create_res = client.post("/api/map/tiles", json={
        "q": 2, "r": 2, "terrain": "mountain", "is_revealed": False
    })
    tile_id = create_res.json()["id"]

    # Update tile to reveal
    update_res = client.put(f"/api/map/tiles/{tile_id}", json={
        "is_revealed": True
    })
    assert update_res.status_code == 200
    assert update_res.json()["is_revealed"] == True

    # Check if player can see it now
    app.dependency_overrides[get_current_active_user] = lambda: User(
        id=2, username="player", email="player@test.com", role="player", is_active=True
    )
    response = client.get("/api/map/tiles")
    # Player should see it now (assuming DB state persists within test or cleaned up)
    # Since this is a new test function, DB might be reset depending on fixture scope.
    # Fixture scope is "function" in conftest.py, so DB is reset.
    # So this test fails if I expect player to see it?
    # No, I just created it in this test.

    data = response.json()
    assert len(data) == 1
    assert data[0]["q"] == 2
