from sqlalchemy.orm import Session
from . import models, schemas
from ..items import service as item_service
from ..characters import models as char_models

def get_mission(db: Session, mission_id: int):
    return db.query(models.Mission).filter(models.Mission.id == mission_id).first()

def get_missions(db: Session, campaign_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Mission).filter(models.Mission.campaign_id == campaign_id).offset(skip).limit(limit).all()

def create_mission(db: Session, mission: schemas.MissionCreate, campaign_id: int):
    db_mission = models.Mission(
        name=mission.name,
        description=mission.description,
        status=mission.status,
        campaign_id=campaign_id
    )
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
                item_service.add_item_to_inventory(db, character_id=character.id, item_id=reward.item_id, quantity=1)

    db.commit()
    return {"message": "Rewards distributed successfully"}
