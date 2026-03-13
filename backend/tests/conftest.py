import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.main import app
from app.dependencies import get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Shared auth fixtures — usable by any test file via pytest dependency injection.
# ---------------------------------------------------------------------------

@pytest.fixture
def campaign(db_session):
    from app.modules.campaigns import models as campaign_models
    camp = campaign_models.Campaign(
        name="Test Campaign",
        discord_guild_id="123456789012345678",
    )
    db_session.add(camp)
    db_session.commit()
    db_session.refresh(camp)
    return camp


def _create_user_with_token(db_session, discord_id: str, username: str, role: str, campaign_id: int):
    """Helper: creates a User + Character + CharacterStats, returns (user, jwt_token)."""
    from app.modules.auth import models as auth_models
    from app.modules.characters import models as char_models
    from app import security

    user = auth_models.User(
        username=username,
        discord_id=discord_id,
        campaign_id=campaign_id,
        role=role,
    )
    db_session.add(user)
    db_session.flush()

    char = char_models.Character(
        name=f"{username}'s Character",
        campaign_id=campaign_id,
        owner_id=user.id,
    )
    db_session.add(char)
    db_session.flush()

    stats = char_models.CharacterStats(character_id=char.id)
    db_session.add(stats)

    user.active_character_id = char.id
    db_session.commit()
    db_session.refresh(user)

    token = security.create_access_token(
        data={"sub": discord_id, "campaign_id": campaign_id, "role": role}
    )
    return user, token


@pytest.fixture
def player_auth_headers(db_session, campaign):
    """Authorization headers for a regular player user."""
    _, token = _create_user_with_token(
        db_session, "player_discord_123", "PlayerUser", "player", campaign.id
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(db_session, campaign):
    """Authorization headers for an admin (DM) user."""
    _, token = _create_user_with_token(
        db_session, "admin_discord_456", "AdminUser", "admin", campaign.id
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def global_token() -> str:
    """
    A 'global' JWT — issued after Discord OAuth but before campaign selection.
    Has no campaign_id, so it should be rejected by campaign-scoped endpoints.
    """
    from app import security
    return security.create_access_token(
        data={"sub": "some_discord_id", "type": "global", "username": "TestUser", "avatar": None}
    )
