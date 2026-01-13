from sqlalchemy.orm import Session
from . import models, schemas
from ... import security
from ..characters import models as char_models

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def get_user_by_discord_id(db: Session, discord_id: str, campaign_id: int):
    return db.query(models.User).filter(
        models.User.discord_id == discord_id,
        models.User.campaign_id == campaign_id
    ).first()

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(
        discord_id=user.discord_id,
        username=user.username,
        # email field removed from model
        avatar_url=user.avatar_url,
        campaign_id=user.campaign_id,
        role=user.role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create a default character for the new user
    character_name = f"{db_user.username}'s Character"
    db_character = char_models.Character(
        name=character_name,
        owner_id=db_user.id,
        campaign_id=user.campaign_id # Important: Character must be in the same campaign
    )
    db.add(db_character)
    db.commit()
    db.refresh(db_character)

    # Create default stats for the new character
    db_stats = char_models.CharacterStats(character_id=db_character.id)
    db.add(db_stats)
    db.commit()
    db.refresh(db_stats)

    # We need to refresh the user to get the character relationship loaded
    db.refresh(db_user)
    return db_user
