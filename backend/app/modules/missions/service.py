from sqlalchemy.orm import Session
from . import models, schemas
from ..characters import models as char_models


def get_mission(db: Session, mission_id: str):
    return db.query(models.Mission).filter(models.Mission.id == mission_id).first()


def get_missions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Mission).offset(skip).limit(limit).all()


def create_mission(db: Session, mission: schemas.MissionCreate):
    db_mission = models.Mission(**mission.model_dump())
    db.add(db_mission)
    db.commit()
    db.refresh(db_mission)
    return db_mission


def add_character_to_mission(db: Session, mission: models.Mission, character: char_models.Character):
    mission.players.append(character)
    db.commit()
    db.refresh(mission)
    return mission


def remove_character_from_mission(db: Session, mission: models.Mission, character: char_models.Character):
    mission.players.remove(character)
    db.commit()
    db.refresh(mission)
    return mission


def update_mission(db: Session, mission: models.Mission, mission_in: schemas.MissionCreate):
    update_data = mission_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(mission, key, value)
    db.commit()
    db.refresh(mission)
    return mission
