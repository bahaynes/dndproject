from sqlalchemy.orm import Session
from . import models, schemas


def get_character(db: Session, character_id: int):
    return db.query(models.Character).filter(models.Character.id == character_id).first()


def list_characters_for_user(db: Session, owner_id: int):
    """Return all characters owned by a specific user."""

    return db.query(models.Character).filter(models.Character.owner_id == owner_id).all()


def create_character(db: Session, character: schemas.CharacterCreate, owner_id: int):
    """Create a character with optional starting stats for the owner."""

    character_data = character.model_dump(exclude={"stats"}, exclude_unset=True)
    stats_data = character.stats.model_dump(exclude_unset=True) if character.stats else {}

    db_character = models.Character(owner_id=owner_id, **character_data)
    db.add(db_character)
    db.flush()  # populate db_character.id for stats relationship

    db_stats = models.CharacterStats(character_id=db_character.id, **stats_data)
    db.add(db_stats)
    db.commit()
    db.refresh(db_character)
    return db_character


def update_character(db: Session, character_id: int, character: schemas.CharacterCreate):
    db_character = get_character(db, character_id)
    if db_character:
        update_data = character.model_dump(exclude_unset=True)
        stats_data = update_data.pop("stats", None)
        for key, value in update_data.items():
            setattr(db_character, key, value)

        if stats_data:
            if db_character.stats:
                for key, value in stats_data.items():
                    setattr(db_character.stats, key, value)
            else:
                db_character.stats = models.CharacterStats(character_id=character_id, **stats_data)
        db.commit()
        db.refresh(db_character)
    return db_character
