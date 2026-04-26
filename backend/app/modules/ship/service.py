from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional

from . import models, schemas
from .models import LEVEL_THRESHOLDS
from ..ledger import service as ledger_service


def compute_level_from_essence(essence: int) -> int:
    """Return highest level unlocked by current cumulative essence."""
    level = 1
    for i, threshold in enumerate(LEVEL_THRESHOLDS):
        if essence >= threshold:
            level = i + 1
    return level


def get_or_create_ship(db: Session, campaign_id: int) -> models.Ship:
    ship = db.query(models.Ship).filter(models.Ship.campaign_id == campaign_id).first()
    if not ship:
        ship = models.Ship(campaign_id=campaign_id)
        db.add(ship)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            ship = db.query(models.Ship).filter(models.Ship.campaign_id == campaign_id).first()
    return ship


def update_ship(db: Session, campaign_id: int, data: schemas.ShipUpdate) -> models.Ship:
    ship = get_or_create_ship(db, campaign_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(ship, field, value)
    # If essence was updated directly, auto-advance level (never decrease)
    if data.essence is not None:
        computed = compute_level_from_essence(ship.essence)
        if computed > ship.level:
            ship.level = computed
    db.commit()
    db.refresh(ship)
    return ship


def adjust_resources(
    db: Session,
    campaign_id: int,
    description: str,
    essence_delta: int = 0,
    gold_delta: int = 0,
    hp_delta: int = 0,
    session_id: Optional[int] = None,
    event_type: str = "ShipAdjustment",
) -> models.Ship:
    ship = get_or_create_ship(db, campaign_id)
    
    # Update Essence
    ship.essence = max(0, ship.essence + essence_delta)
    # Auto-advance level when essence crosses a threshold (never decrease)
    computed = compute_level_from_essence(ship.essence)
    if computed > ship.level:
        ship.level = computed
        
    # Update Gold
    ship.gold = max(0, ship.gold + gold_delta)
    
    # Update HP
    ship.current_hp = max(0, min(ship.max_hp, ship.current_hp + hp_delta))
    
    db.flush()

    snapshot = get_snapshot(ship)
    ledger_service.create_entry(
        db=db,
        campaign_id=campaign_id,
        event_type=event_type,
        description=description,
        essence_delta=essence_delta,
        gold_delta=gold_delta,
        hp_delta=hp_delta,
        session_id=session_id,
        ship_snapshot=snapshot,
    )
    db.flush()
    return ship


def get_snapshot(ship: models.Ship) -> dict:
    return {
        "level": ship.level, 
        "essence": ship.essence,
        "gold": ship.gold,
        "hp": ship.current_hp,
        "max_hp": ship.max_hp
    }
