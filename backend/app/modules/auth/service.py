from sqlalchemy.orm import Session

from . import models, schemas
from ... import security
from ..characters import models as char_models


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
    db_character = char_models.Character(name=character_name, owner_id=db_user.id)
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
