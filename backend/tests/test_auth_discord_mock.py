import pytest
import os
from unittest.mock import AsyncMock, patch, Mock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.modules.campaigns import models as campaign_models
from app.modules.auth import models as auth_models
from app.config import get_settings
from app.dependencies import get_current_user_global

# Setup Test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_override.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db():
    db = TestingSessionLocal()
    yield db
    db.close()

# Mocks
@pytest.fixture
def mock_httpx_client():
    with patch("httpx.AsyncClient") as MockClient:
        mock_instance = AsyncMock()
        MockClient.return_value = mock_instance
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        yield mock_instance

def test_campaign_join_flow(client, db, mock_httpx_client):
    # 1. Create Campaign
    camp = campaign_models.Campaign(name="Joinable", discord_guild_id="55555", dm_role_id="111", player_role_id="222")
    db.add(camp)
    db.commit()

    user_id = "user_123"
    token = "discord_access_token_mock"

    # Mock return for Guild Member check
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"roles": ["222"]}

    # Configure the async get method to return the synchronous mock response
    mock_httpx_client.get.return_value = mock_response

    # For join flow, we also need to verify the user identity.
    original_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_current_user_global] = lambda: {"sub": user_id, "username": "TestUser", "avatar": "av1", "type": "global"}

    try:
        response = client.post(
            "/api/campaigns/join",
            json={"discord_guild_id": "55555", "discord_access_token": token}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["campaign"]["name"] == "Joinable"

        # Verify User Created
        user = db.query(auth_models.User).filter_by(discord_id=user_id).first()
        assert user is not None
        assert user.role == "player"
        assert user.campaign_id == camp.id
    finally:
        app.dependency_overrides = original_overrides
