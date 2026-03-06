from sqlalchemy.orm import Session
from . import models, schemas
from typing import List
from ..maps import service as maps_service, schemas as maps_schemas

def get_campaign(db: Session, campaign_id: int):
    return db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()

def get_campaign_by_guild_id(db: Session, guild_id: str):
    return db.query(models.Campaign).filter(models.Campaign.discord_guild_id == guild_id).first()

def get_all_campaigns(db: Session):
    return db.query(models.Campaign).all()

def get_campaigns_by_guild_ids(db: Session, guild_ids: List[str]):
    return db.query(models.Campaign).filter(models.Campaign.discord_guild_id.in_(guild_ids)).all()

def create_campaign(db: Session, campaign: schemas.CampaignCreate):
    db_campaign = models.Campaign(
        name=campaign.name,
        discord_guild_id=campaign.discord_guild_id,
        dm_role_id=campaign.dm_role_id,
        player_role_id=campaign.player_role_id
    )
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    
    # NEW: Create default World Map upon campaign creation
    default_map = maps_schemas.HexMapCreate(
        name="The Known World",
        width=20,
        height=20,
        hex_size=60
    )
    maps_service.create_map(db, default_map, campaign_id=db_campaign.id, seed=True)
    
    return db_campaign
