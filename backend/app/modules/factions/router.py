from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.orm import Session

from ...dependencies import get_db, get_current_user, get_current_active_admin_user
from ..auth.schemas import User
from . import schemas, service

router = APIRouter()


@router.get("/", response_model=List[schemas.FactionReputation], tags=["Factions"])
def get_reputations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.get_all_reputations(db, campaign_id=current_user.campaign_id)


@router.post("/", response_model=schemas.FactionReputation, tags=["Factions"])
def create_faction(
    data: schemas.FactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user),
):
    return service.create_faction(db, campaign_id=current_user.campaign_id, data=data)


@router.delete("/{faction_name}", status_code=204, tags=["Factions"])
def delete_faction(
    faction_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user),
):
    service.delete_faction(db, campaign_id=current_user.campaign_id, faction_name=faction_name)


@router.post("/{faction_name}/adjust", response_model=schemas.FactionReputation, tags=["Factions"])
def adjust_reputation(
    faction_name: str,
    adjust: schemas.ReputationAdjust,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user),
):
    return service.adjust_reputation(
        db,
        campaign_id=current_user.campaign_id,
        faction_name=faction_name,
        adjust=adjust,
    )
