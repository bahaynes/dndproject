from sqlalchemy.orm import Session
from . import models, schemas
from ..characters import models as char_models

def get_game_session(db: Session, session_id: int):
    return db.query(models.GameSession).filter(models.GameSession.id == session_id).first()

def get_game_sessions(db: Session, campaign_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.GameSession).filter(
        models.GameSession.campaign_id == campaign_id
    ).offset(skip).limit(limit).all()

def create_game_session(db: Session, session: schemas.GameSessionCreate, campaign_id: int):
    db_session = models.GameSession(**session.model_dump(), campaign_id=campaign_id)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def add_character_to_game_session(db: Session, session: models.GameSession, character: char_models.Character):
    session.players.append(character)
    db.commit()
    db.refresh(session)
    return session

def remove_character_from_game_session(db: Session, session: models.GameSession, character: char_models.Character):
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
