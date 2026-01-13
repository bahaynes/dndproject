from sqlalchemy.orm import Session
from . import models, schemas

def get_campaign(db: Session, campaign_id: int):
    return db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()

def get_campaign_by_guild_id(db: Session, guild_id: str):
    return db.query(models.Campaign).filter(models.Campaign.discord_guild_id == guild_id).first()

def get_all_campaigns(db: Session):
    return db.query(models.Campaign).all()

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
    return db_campaign
