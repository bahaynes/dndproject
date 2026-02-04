from sqlalchemy.orm import Session
from sqlalchemy import or_
import datetime
from . import models, schemas
from ..items import service as item_service
from ..characters import models as char_models

def get_mission(db: Session, mission_id: int):
    return db.query(models.Mission).filter(models.Mission.id == mission_id).first()

def get_missions(db: Session, campaign_id: int, skip: int = 0, limit: int = 100,
                 tier: str = None, region: str = None,
                 include_retired: bool = False, include_hidden: bool = False):
    query = db.query(models.Mission).filter(models.Mission.campaign_id == campaign_id)

    if not include_retired:
        query = query.filter(models.Mission.is_retired == False)

    if not include_hidden:
        query = query.filter(models.Mission.is_discoverable == True)

    if tier:
        query = query.filter(models.Mission.tier == tier)

    if region:
        query = query.filter(models.Mission.region == region)

    return query.offset(skip).limit(limit).all()

def is_mission_selectable(mission: models.Mission):
    if mission.is_retired:
        return False, "Mission is retired"

    if mission.last_run_date:
        now = datetime.datetime.utcnow()
        cooldown_end = mission.last_run_date + datetime.timedelta(days=mission.cooldown_days)
        if now < cooldown_end:
            return False, f"In cooldown until {cooldown_end.date()}"

    return True, None

def create_mission(db: Session, mission: schemas.MissionCreate, campaign_id: int):
    db_mission = models.Mission(
        name=mission.name,
        description=mission.description,
        status=mission.status,
        campaign_id=campaign_id,
        tier=mission.tier,
        region=mission.region,
        cooldown_days=mission.cooldown_days,
        is_retired=mission.is_retired,
        is_discoverable=mission.is_discoverable,
        prerequisite_id=mission.prerequisite_id
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

def update_mission(db: Session, mission: models.Mission, mission_update: schemas.MissionCreate):
    mission.name = mission_update.name
    mission.description = mission_update.description
    mission.status = mission_update.status
    mission.tier = mission_update.tier
    mission.region = mission_update.region
    mission.cooldown_days = mission_update.cooldown_days
    mission.is_retired = mission_update.is_retired
    mission.is_discoverable = mission_update.is_discoverable
    mission.prerequisite_id = mission_update.prerequisite_id

    # Update rewards (simplest way: delete old, add new)
    db.query(models.MissionReward).filter(models.MissionReward.mission_id == mission.id).delete()
    for reward_in in mission_update.rewards:
        db_reward = models.MissionReward(
            mission_id=mission.id,
            **reward_in.model_dump()
        )
        db.add(db_reward)

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
