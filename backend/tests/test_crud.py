import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import crud, models, schemas
from app.database import Base
from datetime import datetime

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Setup the database
Base.metadata.create_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """
    Create a new database session for each test function.
    This fixture will also create all tables and drop them after the test.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

def test_create_and_get_user(db_session):
    # Create user
    user_in = schemas.UserCreate(username="testuser", email="test@example.com", password="password", role="player")
    db_user = crud.create_user(db_session, user_in)

    # Test get_user
    retrieved_user = crud.get_user(db_session, db_user.id)
    assert retrieved_user
    assert retrieved_user.id == db_user.id
    assert retrieved_user.username == "testuser"

    # Test get_user_by_username
    retrieved_user_by_username = crud.get_user_by_username(db_session, "testuser")
    assert retrieved_user_by_username
    assert retrieved_user_by_username.username == "testuser"

    # Test get_user_by_email
    retrieved_user_by_email = crud.get_user_by_email(db_session, "test@example.com")
    assert retrieved_user_by_email
    assert retrieved_user_by_email.email == "test@example.com"

def test_get_users(db_session):
    # Create multiple users
    crud.create_user(db_session, schemas.UserCreate(username="user1", email="user1@example.com", password="password", role="player"))
    crud.create_user(db_session, schemas.UserCreate(username="user2", email="user2@example.com", password="password", role="player"))

    users = crud.get_users(db_session)
    assert len(users) == 2
    assert users[0].username == "user1"
    assert users[1].username == "user2"

def test_character_crud(db_session):
    # Create a user to own the character
    user_in = schemas.UserCreate(username="charowner", email="charowner@example.com", password="password", role="player")
    db_user = crud.create_user(db_session, user_in)

    # Test get_character
    character = crud.get_character(db_session, db_user.character.id)
    assert character is not None
    assert character.name == "charowner's Character"
    assert character.owner_id == db_user.id

    # Test update_character
    character_update = schemas.CharacterCreate(name="New Name")
    updated_character = crud.update_character(db_session, character.id, character_update)
    assert updated_character.name == "New Name"

def test_item_crud(db_session):
    # Test create_item
    item_in = schemas.ItemCreate(name="Test Item", description="A test item")
    db_item = crud.create_item(db_session, item_in)
    assert db_item.name == "Test Item"

    # Test get_item
    retrieved_item = crud.get_item(db_session, db_item.id)
    assert retrieved_item
    assert retrieved_item.id == db_item.id
    assert retrieved_item.name == "Test Item"

    # Test get_items
    crud.create_item(db_session, schemas.ItemCreate(name="Test Item 2", description="Another test item"))
    items = crud.get_items(db_session)
    assert len(items) == 2
    assert items[0].name == "Test Item"
    assert items[1].name == "Test Item 2"

def test_inventory_crud(db_session):
    # Create a user and an item
    user_in = schemas.UserCreate(username="invowner", email="invowner@example.com", password="password", role="player")
    db_user = crud.create_user(db_session, user_in)
    item_in = schemas.ItemCreate(name="Inventory Item", description="An item for inventory")
    db_item = crud.create_item(db_session, item_in)

    # Test add_item_to_inventory
    inventory_item = crud.add_item_to_inventory(db_session, db_user.character.id, db_item.id, 5)
    assert inventory_item.quantity == 5
    assert inventory_item.character_id == db_user.character.id
    assert inventory_item.item_id == db_item.id

    # Test remove_item_from_inventory
    crud.remove_item_from_inventory(db_session, inventory_item.id, 2)
    assert inventory_item.quantity == 3

    # Test removing all items
    result = crud.remove_item_from_inventory(db_session, inventory_item.id, 3)
    assert result is None
    retrieved_inventory_item = db_session.query(models.InventoryItem).filter(models.InventoryItem.id == inventory_item.id).first()
    assert retrieved_inventory_item is None

def test_store_crud(db_session):
    # Create a user, item and store item
    user_in = schemas.UserCreate(username="buyer", email="buyer@example.com", password="password", role="player")
    db_user = crud.create_user(db_session, user_in)
    item_in = schemas.ItemCreate(name="Store Item", description="An item for the store")
    db_item = crud.create_item(db_session, item_in)
    store_item_in = schemas.StoreItemCreate(item_id=db_item.id, price=100, quantity_available=10)
    db_store_item = crud.create_store_item(db_session, store_item_in)

    # Test get_store_item
    retrieved_store_item = crud.get_store_item(db_session, db_store_item.id)
    assert retrieved_store_item
    assert retrieved_store_item.id == db_store_item.id
    assert retrieved_store_item.price == 100

    # Test get_store_items
    store_items = crud.get_store_items(db_session)
    assert len(store_items) == 1

    # Test purchase_item
    db_user.character.stats.scrip = 500
    db_session.commit()
    result = crud.purchase_item(db_session, db_user.character, db_store_item, 3)
    assert result["message"] == "Purchase successful"
    assert db_user.character.stats.scrip == 200
    assert db_store_item.quantity_available == 7

    # Test purchase with not enough scrip
    result = crud.purchase_item(db_session, db_user.character, db_store_item, 3)
    assert result["error"] == "Not enough scrip"

def test_mission_crud(db_session):
    user_in = schemas.UserCreate(username="missionrunner", email="missionrunner@example.com", password="password", role="player")
    db_user = crud.create_user(db_session, user_in)
    mission_in = schemas.MissionCreate(name="Test Mission", description="A test mission", status="Active", rewards=[])
    db_mission = crud.create_mission(db_session, mission_in)

    # Test get_mission
    retrieved_mission = crud.get_mission(db_session, db_mission.id)
    assert retrieved_mission
    assert retrieved_mission.name == "Test Mission"

    # Test get_missions
    missions = crud.get_missions(db_session)
    assert len(missions) == 1

    # Test add_character_to_mission
    crud.add_character_to_mission(db_session, db_mission, db_user.character)
    assert db_user.character in db_mission.players

    # Test remove_character_from_mission
    crud.remove_character_from_mission(db_session, db_mission, db_user.character)
    assert db_user.character not in db_mission.players

    # Test update_mission_status
    crud.update_mission_status(db_session, db_mission, "Completed")
    assert db_mission.status == "Completed"

    # Test distribute_mission_rewards
    item_in = schemas.ItemCreate(name="Reward Item", description="A reward item")
    db_item = crud.create_item(db_session, item_in)
    db_mission.rewards.append(models.MissionReward(mission_id=db_mission.id, xp=100, scrip=50, item_id=db_item.id))
    crud.add_character_to_mission(db_session, db_mission, db_user.character)
    db_session.commit()

    result = crud.distribute_mission_rewards(db_session, db_mission)
    assert result["message"] == "Rewards distributed successfully"
    assert db_user.character.stats.xp == 100
    assert db_user.character.stats.scrip == 50

    inventory_item = db_session.query(models.InventoryItem).filter(models.InventoryItem.character_id == db_user.character.id, models.InventoryItem.item_id == db_item.id).first()
    assert inventory_item is not None
    assert inventory_item.quantity == 1

def test_game_session_crud(db_session):
    user_in = schemas.UserCreate(username="sessionplayer", email="sessionplayer@example.com", password="password", role="player")
    db_user = crud.create_user(db_session, user_in)
    session_in = schemas.GameSessionCreate(name="Test Session", description="A test session", status="Open", session_date=datetime.now())
    db_session_obj = crud.create_game_session(db_session, session_in)

    # Test get_game_session
    retrieved_session = crud.get_game_session(db_session, db_session_obj.id)
    assert retrieved_session
    assert retrieved_session.name == "Test Session"

    # Test get_game_sessions
    sessions = crud.get_game_sessions(db_session)
    assert len(sessions) == 1

    # Test add_character_to_game_session
    crud.add_character_to_game_session(db_session, db_session_obj, db_user.character)
    assert db_user.character in db_session_obj.players

    # Test remove_character_from_game_session
    crud.remove_character_from_game_session(db_session, db_session_obj, db_user.character)
    assert db_user.character not in db_session_obj.players

    # Test update_game_session
    session_update = schemas.GameSessionCreate(name="New Session Name", description="New description", status="Closed", session_date=datetime.now())
    updated_session = crud.update_game_session(db_session, db_session_obj, session_update)
    assert updated_session.name == "New Session Name"
    assert updated_session.status == "Closed"

def test_data_import_export(db_session):
    # Create some data
    crud.create_user(db_session, schemas.UserCreate(username="exportuser", email="exportuser@example.com", password="password", role="player"))
    crud.create_item(db_session, schemas.ItemCreate(name="Export Item", description="An item for export"))

    # Test export_game_data
    exported_data = crud.export_game_data(db_session)
    assert len(exported_data.users) == 1
    assert len(exported_data.items) == 1
    assert exported_data.users[0].username == "exportuser"
    assert exported_data.items[0].name == "Export Item"

    # Test import_game_data (which currently just wipes the data)
    result = crud.import_game_data(db_session, exported_data)
    assert result["message"] == "Data wipe successful. Full import is not yet implemented."

    users = crud.get_users(db_session)
    assert len(users) == 0
    items = crud.get_items(db_session)
    assert len(items) == 0
