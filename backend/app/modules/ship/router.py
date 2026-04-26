from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...dependencies import get_db, get_current_active_user, get_current_active_admin_user
from ..auth.schemas import User
from . import schemas, service

router = APIRouter()


@router.get("/", response_model=schemas.ShipOut, tags=["Ship"])
def get_ship(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    ship = service.get_or_create_ship(db, campaign_id=current_user.campaign_id)
    db.commit()
    return ship


@router.put("/", response_model=schemas.ShipOut, tags=["Ship"])
def update_ship(
    data: schemas.ShipUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user),
):
    return service.update_ship(db, campaign_id=current_user.campaign_id, data=data)


@router.post("/adjust", response_model=schemas.ShipOut, tags=["Ship"])
def adjust_ship(
    data: schemas.ShipAdjust,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user),
):
    ship = service.adjust_resources(
        db,
        campaign_id=current_user.campaign_id,
        description=data.description,
        essence_delta=data.essence_delta,
        gold_delta=data.gold_delta,
        hp_delta=data.hp_delta,
        event_type="AdminAdjustment",
    )
    db.commit()
    db.refresh(ship)
    return ship
