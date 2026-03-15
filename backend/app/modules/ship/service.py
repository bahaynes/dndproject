from sqlalchemy.orm import Session
from typing import Optional

from . import models, schemas
from ..ledger import service as ledger_service


def get_or_create_ship(db: Session, campaign_id: int) -> models.Ship:
    ship = db.query(models.Ship).filter(models.Ship.campaign_id == campaign_id).first()
    if not ship:
        ship = models.Ship(campaign_id=campaign_id)
        db.add(ship)
        db.commit()
        db.refresh(ship)
    return ship


def update_ship(db: Session, campaign_id: int, data: schemas.ShipUpdate) -> models.Ship:
    ship = get_or_create_ship(db, campaign_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(ship, field, value)
    db.commit()
    db.refresh(ship)
    return ship


def adjust_resources(
    db: Session,
    campaign_id: int,
    description: str,
    fuel_delta: int = 0,
    crystal_delta: int = 0,
    credit_delta: int = 0,
    session_id: Optional[int] = None,
    event_type: str = "ShipAdjustment",
) -> models.Ship:
    ship = get_or_create_ship(db, campaign_id)
    ship.fuel = max(0, ship.fuel + fuel_delta)
    ship.crystals = max(0, ship.crystals + crystal_delta)
    ship.credits = max(0, ship.credits + credit_delta)
    db.flush()

    snapshot = {
        "level": ship.level,
        "fuel": ship.fuel,
        "crystals": ship.crystals,
        "credits": ship.credits,
    }
    ledger_service.create_entry(
        db=db,
        campaign_id=campaign_id,
        event_type=event_type,
        description=description,
        fuel_delta=fuel_delta,
        crystal_delta=crystal_delta,
        credit_delta=credit_delta,
        session_id=session_id,
        ship_snapshot=snapshot,
    )
    db.commit()
    db.refresh(ship)
    return ship


def get_snapshot(ship: models.Ship) -> dict:
    return {
        "level": ship.level,
        "fuel": ship.fuel,
        "crystals": ship.crystals,
        "credits": ship.credits,
    }
