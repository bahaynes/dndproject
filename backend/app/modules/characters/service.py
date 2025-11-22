from sqlalchemy.orm import Session
from . import models, schemas

def get_character(db: Session, character_id: int):
    return db.query(models.Character).filter(models.Character.id == character_id).first()

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
