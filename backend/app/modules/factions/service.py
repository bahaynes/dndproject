from fastapi import HTTPException
from sqlalchemy.orm import Session
from . import models, schemas


def get_reputation(db: Session, campaign_id: int, faction_name: str) -> models.FactionReputation:
    rep = (
        db.query(models.FactionReputation)
        .filter_by(campaign_id=campaign_id, faction_name=faction_name)
        .first()
    )
    if not rep:
        raise HTTPException(status_code=404, detail=f"Faction '{faction_name}' not found")
    return rep


def get_all_reputations(db: Session, campaign_id: int) -> list[models.FactionReputation]:
    return (
        db.query(models.FactionReputation)
        .filter_by(campaign_id=campaign_id)
        .all()
    )


def create_faction(
    db: Session,
    campaign_id: int,
    data: schemas.FactionCreate,
) -> models.FactionReputation:
    existing = (
        db.query(models.FactionReputation)
        .filter_by(campaign_id=campaign_id, faction_name=data.faction_name)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail=f"Faction '{data.faction_name}' already exists")
    rep = models.FactionReputation(
        campaign_id=campaign_id,
        faction_name=data.faction_name,
        color=data.color,
        description=data.description,
        level=0,
    )
    db.add(rep)
    db.commit()
    db.refresh(rep)
    return rep


def delete_faction(db: Session, campaign_id: int, faction_name: str) -> None:
    rep = get_reputation(db, campaign_id, faction_name)
    db.delete(rep)
    db.commit()


def adjust_reputation(
    db: Session,
    campaign_id: int,
    faction_name: str,
    adjust: schemas.ReputationAdjust,
) -> models.FactionReputation:
    rep = get_reputation(db, campaign_id, faction_name)

    new_level = max(-5, min(5, rep.level + adjust.delta))
    rep.level = new_level

    event = models.FactionReputationEvent(
        reputation_id=rep.id,
        delta=adjust.delta,
        description=adjust.description,
        session_id=adjust.session_id,
    )
    db.add(event)
    db.commit()
    db.refresh(rep)
    return rep
