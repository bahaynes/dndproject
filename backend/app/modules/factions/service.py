from sqlalchemy.orm import Session
from . import models, schemas

FACTIONS = ["Kathedral", "Vastarei"]


def get_or_create_reputation(db: Session, campaign_id: int, faction_name: str) -> models.FactionReputation:
    rep = (
        db.query(models.FactionReputation)
        .filter_by(campaign_id=campaign_id, faction_name=faction_name)
        .first()
    )
    if not rep:
        rep = models.FactionReputation(campaign_id=campaign_id, faction_name=faction_name, level=0)
        db.add(rep)
        db.commit()
        db.refresh(rep)
    return rep


def get_all_reputations(db: Session, campaign_id: int) -> list[models.FactionReputation]:
    # Ensure both factions exist before returning
    for faction in FACTIONS:
        get_or_create_reputation(db, campaign_id, faction)
    return (
        db.query(models.FactionReputation)
        .filter_by(campaign_id=campaign_id)
        .all()
    )


def adjust_reputation(
    db: Session,
    campaign_id: int,
    faction_name: str,
    adjust: schemas.ReputationAdjust,
) -> models.FactionReputation:
    rep = get_or_create_reputation(db, campaign_id, faction_name)

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
