import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
# Models
from app.modules.auth import models as auth_models
from app.modules.characters import models as char_models
from app.modules.items import models as item_models
from app.modules.missions import models as mission_models
from app.modules.sessions import models as session_models

# Schemas
from app.modules.auth import schemas as auth_schemas
from app.modules.characters import schemas as char_schemas
from app.modules.items import schemas as item_schemas
from app.modules.missions import schemas as mission_schemas
from app.modules.sessions import schemas as session_schemas
from app.modules.admin import schemas as admin_schemas

# Services (CRUD)
from app.modules.auth import service as auth_service
from app.modules.characters import service as char_service
from app.modules.items import service as item_service
from app.modules.missions import service as mission_service
from app.modules.sessions import service as session_service
from app.modules.admin import service as admin_service

from datetime import datetime

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Setup the database
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

def test_create_and_get_user(db_session):
    user_in = auth_schemas.UserCreate(username="testuser", email="test@example.com", password="password", role="player")
    db_user = auth_service.create_user(db_session, user_in)

    retrieved_user = auth_service.get_user(db_session, db_user.id)
    assert retrieved_user
    assert retrieved_user.id == db_user.id
    assert retrieved_user.username == "testuser"

    retrieved_user_by_username = auth_service.get_user_by_username(db_session, "testuser")
    assert retrieved_user_by_username
    assert retrieved_user_by_username.username == "testuser"

    retrieved_user_by_email = auth_service.get_user_by_email(db_session, "test@example.com")
    assert retrieved_user_by_email
    assert retrieved_user_by_email.email == "test@example.com"

def test_get_users(db_session):
    auth_service.create_user(db_session, auth_schemas.UserCreate(username="user1", email="user1@example.com", password="password", role="player"))
    auth_service.create_user(db_session, auth_schemas.UserCreate(username="user2", email="user2@example.com", password="password", role="player"))

    users = auth_service.get_users(db_session)
    assert len(users) == 2
    assert users[0].username == "user1"
    assert users[1].username == "user2"

def test_character_crud(db_session):
    user_in = auth_schemas.UserCreate(username="charowner", email="charowner@example.com", password="password", role="player")
    db_user = auth_service.create_user(db_session, user_in)

    character = char_service.get_character(db_session, db_user.character.id)
    assert character is not None
    assert character.name == "charowner's Character"
    assert character.owner_id == db_user.id

    character_update = char_schemas.CharacterCreate(name="New Name")
    updated_character = char_service.update_character(db_session, character.id, character_update)
    assert updated_character.name == "New Name"

def test_item_crud(db_session):
    item_in = item_schemas.ItemCreate(name="Test Item", description="A test item")
    db_item = item_service.create_item(db_session, item_in)
    assert db_item.name == "Test Item"

    retrieved_item = item_service.get_item(db_session, db_item.id)
    assert retrieved_item
    assert retrieved_item.id == db_item.id
    assert retrieved_item.name == "Test Item"

    item_service.create_item(db_session, item_schemas.ItemCreate(name="Test Item 2", description="Another test item"))
    items = item_service.get_items(db_session)
    assert len(items) == 2
    assert items[0].name == "Test Item"
    assert items[1].name == "Test Item 2"

def test_inventory_crud(db_session):
    user_in = auth_schemas.UserCreate(username="invowner", email="invowner@example.com", password="password", role="player")
    db_user = auth_service.create_user(db_session, user_in)
    item_in = item_schemas.ItemCreate(name="Inventory Item", description="An item for inventory")
    db_item = item_service.create_item(db_session, item_in)

    inventory_item = item_service.add_item_to_inventory(db_session, db_user.character.id, db_item.id, 5)
    assert inventory_item.quantity == 5
    assert inventory_item.character_id == db_user.character.id
    assert inventory_item.item_id == db_item.id

    item_service.remove_item_from_inventory(db_session, inventory_item.id, 2)
    assert inventory_item.quantity == 3

    result = item_service.remove_item_from_inventory(db_session, inventory_item.id, 3)
    assert result is None
    retrieved_inventory_item = db_session.query(item_models.InventoryItem).filter(item_models.InventoryItem.id == inventory_item.id).first()
    assert retrieved_inventory_item is None

def test_store_crud(db_session):
    user_in = auth_schemas.UserCreate(username="buyer", email="buyer@example.com", password="password", role="player")
    db_user = auth_service.create_user(db_session, user_in)
    item_in = item_schemas.ItemCreate(name="Store Item", description="An item for the store")
    db_item = item_service.create_item(db_session, item_in)
    store_item_in = item_schemas.StoreItemCreate(item_id=db_item.id, price=100, quantity_available=10)
    db_store_item = item_service.create_store_item(db_session, store_item_in)

    retrieved_store_item = item_service.get_store_item(db_session, db_store_item.id)
    assert retrieved_store_item
    assert retrieved_store_item.id == db_store_item.id
    assert retrieved_store_item.price == 100

    store_items = item_service.get_store_items(db_session)
    assert len(store_items) == 1

    db_user.character.stats.scrip = 500
    db_session.commit()
    result = item_service.purchase_item(db_session, db_user.character, db_store_item, 3)
    assert result["message"] == "Purchase successful"
    assert db_user.character.stats.scrip == 200
    assert db_store_item.quantity_available == 7

    result = item_service.purchase_item(db_session, db_user.character, db_store_item, 3)
    assert result["error"] == "Not enough scrip"

def test_mission_crud(db_session):
    user_in = auth_schemas.UserCreate(username="missionrunner", email="missionrunner@example.com", password="password", role="player")
    db_user = auth_service.create_user(db_session, user_in)
    mission_in = mission_schemas.MissionCreate(name="Test Mission", description="A test mission", status="Active", rewards=[])
    db_mission = mission_service.create_mission(db_session, mission_in)

    retrieved_mission = mission_service.get_mission(db_session, db_mission.id)
    assert retrieved_mission
    assert retrieved_mission.name == "Test Mission"

    missions = mission_service.get_missions(db_session)
    assert len(missions) == 1

    mission_service.add_character_to_mission(db_session, db_mission, db_user.character)
    assert db_user.character in db_mission.players

    mission_service.remove_character_from_mission(db_session, db_mission, db_user.character)
    assert db_user.character not in db_mission.players

    mission_service.update_mission_status(db_session, db_mission, "Completed")
    assert db_mission.status == "Completed"

    item_in = item_schemas.ItemCreate(name="Reward Item", description="A reward item")
    db_item = item_service.create_item(db_session, item_in)
    db_mission.rewards.append(mission_models.MissionReward(mission_id=db_mission.id, xp=100, scrip=50, item_id=db_item.id))
    mission_service.add_character_to_mission(db_session, db_mission, db_user.character)
    db_session.commit()

    result = mission_service.distribute_mission_rewards(db_session, db_mission)
    assert result["message"] == "Rewards distributed successfully"
    assert db_user.character.stats.xp == 100
    assert db_user.character.stats.scrip == 50

    inventory_item = db_session.query(item_models.InventoryItem).filter(item_models.InventoryItem.character_id == db_user.character.id, item_models.InventoryItem.item_id == db_item.id).first()
    assert inventory_item is not None
    assert inventory_item.quantity == 1

def test_game_session_crud(db_session):
    user_in = auth_schemas.UserCreate(username="sessionplayer", email="sessionplayer@example.com", password="password", role="player")
    db_user = auth_service.create_user(db_session, user_in)
    session_in = session_schemas.GameSessionCreate(name="Test Session", description="A test session", status="Open", session_date=datetime.now())
    db_session_obj = session_service.create_game_session(db_session, session_in)

    retrieved_session = session_service.get_game_session(db_session, db_session_obj.id)
    assert retrieved_session
    assert retrieved_session.name == "Test Session"

    sessions = session_service.get_game_sessions(db_session)
    assert len(sessions) == 1

    session_service.add_character_to_game_session(db_session, db_session_obj, db_user.character)
    assert db_user.character in db_session_obj.players

    session_service.remove_character_from_game_session(db_session, db_session_obj, db_user.character)
    assert db_user.character not in db_session_obj.players

    session_update = session_schemas.GameSessionCreate(name="New Session Name", description="New description", status="Closed", session_date=datetime.now())
    updated_session = session_service.update_game_session(db_session, db_session_obj, session_update)
    assert updated_session.name == "New Session Name"
    assert updated_session.status == "Closed"

def test_data_import_export(db_session):
    auth_service.create_user(db_session, auth_schemas.UserCreate(username="exportuser", email="exportuser@example.com", password="password", role="player"))
    item_service.create_item(db_session, item_schemas.ItemCreate(name="Export Item", description="An item for export"))

    exported_data = admin_service.export_game_data(db_session)
    assert len(exported_data.users) == 1
    assert len(exported_data.items) == 1
    assert exported_data.users[0].username == "exportuser"
    assert exported_data.items[0].name == "Export Item"

    result = admin_service.import_game_data(db_session, exported_data)
    assert result["message"] == "Data wipe successful. Full import is not yet implemented."

    users = auth_service.get_users(db_session)
    assert len(users) == 0
    items = item_service.get_items(db_session)
    assert len(items) == 0
