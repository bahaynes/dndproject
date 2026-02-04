from sqlalchemy.orm import Session
from . import models, schemas

def get_character(db: Session, character_id: int):
    return db.query(models.Character).filter(models.Character.id == character_id).first()

def update_character(db: Session, character_id: int, character: schemas.CharacterCreate):
    db_character = get_character(db, character_id)
    if db_character:
        update_data = character.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_character, key, value)
        db.commit()
        db.refresh(db_character)
    return db_character

def create_character(db: Session, character: schemas.CharacterCreate, owner_id: int, campaign_id: int):
    db_character = models.Character(
        **character.model_dump(),
        owner_id=owner_id,
        campaign_id=campaign_id
    )
    db.add(db_character)
    db.commit()
    db.refresh(db_character)
    
    # Add stats
    db_stats = models.CharacterStats(character_id=db_character.id)
    db.add(db_stats)
    db.commit()
    db.refresh(db_character)
    
    return db_character
