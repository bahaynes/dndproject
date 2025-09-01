from sqlalchemy.orm import Session

from . import models, schemas, security


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create a default character for the new user
    character_name = f"{db_user.username}'s Character"
    db_character = models.Character(name=character_name, owner_id=db_user.id)
    db.add(db_character)
    db.commit()
    db.refresh(db_character)

    # Create default stats for the new character
    db_stats = models.CharacterStats(character_id=db_character.id)
    db.add(db_stats)
    db.commit()
    db.refresh(db_stats)

    # We need to refresh the user to get the character relationship loaded
    db.refresh(db_user)
    return db_user

def get_character(db: Session, character_id: int):
    return db.query(models.Character).filter(models.Character.id == character_id).first()


def update_character(db: Session, character_id: int, character: schemas.CharacterUpdate):
    db_character = get_character(db, character_id)
    if db_character:
        update_data = character.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_character, key, value)
        db.commit()
        db.refresh(db_character)
    return db_character


def update_character_image_url(db: Session, character_id: int, image_url: str):
    db_character = get_character(db, character_id)
    if db_character:
        db_character.image_url = image_url
        db.commit()
        db.refresh(db_character)
    return db_character


# Item CRUD
def get_item(db: Session, item_id: int):
    return db.query(models.Item).filter(models.Item.id == item_id).first()

def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Item).offset(skip).limit(limit).all()

def create_item(db: Session, item: schemas.ItemCreate):
    db_item = models.Item(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

# Inventory CRUD
def add_item_to_inventory(db: Session, character_id: int, item_id: int, quantity: int = 1):
    # Check if the item already exists in the character's inventory
    db_inventory_item = db.query(models.InventoryItem).filter(
        models.InventoryItem.character_id == character_id,
        models.InventoryItem.item_id == item_id
    ).first()

    if db_inventory_item:
        db_inventory_item.quantity += quantity
    else:
        db_inventory_item = models.InventoryItem(
            character_id=character_id,
            item_id=item_id,
            quantity=quantity
        )
        db.add(db_inventory_item)

    db.commit()
    db.refresh(db_inventory_item)
    return db_inventory_item

def remove_item_from_inventory(db: Session, inventory_item_id: int, quantity: int = 1):
    db_inventory_item = db.query(models.InventoryItem).filter(models.InventoryItem.id == inventory_item_id).first()
    if not db_inventory_item:
        return None

    db_inventory_item.quantity -= quantity
    if db_inventory_item.quantity <= 0:
        db.delete(db_inventory_item)
        db.commit()
        return None # Item removed completely

    db.commit()
    db.refresh(db_inventory_item)
    return db_inventory_item

# Store CRUD
def get_store_item(db: Session, store_item_id: int):
    return db.query(models.StoreItem).filter(models.StoreItem.id == store_item_id).first()

def get_store_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.StoreItem).offset(skip).limit(limit).all()

def create_store_item(db: Session, store_item: schemas.StoreItemCreate):
    db_store_item = models.StoreItem(**store_item.model_dump())
    db.add(db_store_item)
    db.commit()
    db.refresh(db_store_item)
    return db_store_item

def purchase_item(db: Session, character: models.Character, store_item: models.StoreItem, quantity: int):
    if store_item.price * quantity > character.stats.scrip:
        return {"error": "Not enough scrip"}

    if store_item.quantity_available != -1 and store_item.quantity_available < quantity:
        return {"error": "Not enough items in stock"}

    # Deduct scrip
    character.stats.scrip -= store_item.price * quantity

    # Decrement store quantity if not infinite
    if store_item.quantity_available != -1:
        store_item.quantity_available -= quantity

    # Add item to character's inventory
    add_item_to_inventory(db, character_id=character.id, item_id=store_item.item_id, quantity=quantity)

    db.commit()
    return {"message": "Purchase successful"}


# Mission CRUD
def get_mission(db: Session, mission_id: int):
    return db.query(models.Mission).filter(models.Mission.id == mission_id).first()

def get_missions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Mission).offset(skip).limit(limit).all()

def create_mission(db: Session, mission: schemas.MissionCreate):
    db_mission = models.Mission(name=mission.name, description=mission.description, status=mission.status)
    db.add(db_mission)
    db.commit()
    # Now that the mission has an ID, create the rewards
    for reward_in in mission.rewards:
        db_reward = models.MissionReward(
            mission_id=db_mission.id,
            **reward_in.model_dump()
        )
        db.add(db_reward)
    db.commit()
    db.refresh(db_mission)
    return db_mission

def add_character_to_mission(db: Session, mission: models.Mission, character: models.Character):
    mission.players.append(character)
    db.commit()
    db.refresh(mission)
    return mission

def remove_character_from_mission(db: Session, mission: models.Mission, character: models.Character):
    mission.players.remove(character)
    db.commit()
    db.refresh(mission)
    return mission

def update_mission_status(db: Session, mission: models.Mission, status: str):
    mission.status = status
    db.commit()
    db.refresh(mission)
    return mission

def distribute_mission_rewards(db: Session, mission: models.Mission):
    if mission.status != "Completed":
        return {"error": "Mission is not completed yet"}

    for character in mission.players:
        for reward in mission.rewards:
            if reward.xp:
                character.stats.xp += reward.xp
            if reward.scrip:
                character.stats.scrip += reward.scrip
            if reward.item_id:
                add_item_to_inventory(db, character_id=character.id, item_id=reward.item_id, quantity=1)

    db.commit()
    return {"message": "Rewards distributed successfully"}


# Game Session CRUD
def get_game_session(db: Session, session_id: int):
    return db.query(models.GameSession).filter(models.GameSession.id == session_id).first()

def get_game_sessions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.GameSession).offset(skip).limit(limit).all()

def create_game_session(db: Session, session: schemas.GameSessionCreate):
    db_session = models.GameSession(**session.model_dump())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def add_character_to_game_session(db: Session, session: models.GameSession, character: models.Character):
    session.players.append(character)
    db.commit()
    db.refresh(session)
    return session


# Data Import/Export CRUD
def export_game_data(db: Session) -> schemas.GameDataExport:
    users = db.query(models.User).all()
    items = db.query(models.Item).all()
    store_items = db.query(models.StoreItem).all()
    missions = db.query(models.Mission).all()
    game_sessions = db.query(models.GameSession).all()

    # Note: This export is simplified. For a full backup, you'd want to
    # serialize all tables, including association tables, and be careful
    # about object relationships.
    return schemas.GameDataExport(
        users=users,
        items=items,
        store_items=store_items,
        missions=missions,
        game_sessions=game_sessions,
    )

def import_game_data(db: Session, data: schemas.GameDataExport):
    # This is a very destructive operation.
    # For a real application, you'd want backups and more safety checks.
    # This is a simplified implementation for MVP.

    # Wipe existing data in reverse order of dependency
    db.execute(models.game_session_players.delete())
    db.execute(models.mission_players.delete())
    db.query(models.InventoryItem).delete()
    db.query(models.StoreItem).delete()
    db.query(models.MissionReward).delete()
    db.query(models.GameSession).delete()
    db.query(models.Mission).delete()
    db.query(models.Item).delete()
    db.query(models.CharacterStats).delete()
    db.query(models.Character).delete()
    db.query(models.User).delete()
    db.commit()

    # A full import implementation is very complex due to relationships and password hashing.
    # This is a placeholder to demonstrate the wipe-and-reload pattern.
    # In a real scenario, you would iterate through data.users, data.items, etc.,
    # and carefully reconstruct the database, handling all foreign key relationships.

    # For now, we will just wipe the data.

    return {"message": "Data wipe successful. Full import is not yet implemented."}

def remove_character_from_game_session(db: Session, session: models.GameSession, character: models.Character):
    session.players.remove(character)
    db.commit()
    db.refresh(session)
    return session

def update_game_session(db: Session, session: models.GameSession, session_update: schemas.GameSessionCreate):
    update_data = session_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(session, key, value)
    db.commit()
    db.refresh(session)
    return session
