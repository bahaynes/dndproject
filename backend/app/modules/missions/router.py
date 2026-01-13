from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from ...dependencies import get_db, get_current_active_user, get_current_active_admin_user, get_current_user
from ..auth.schemas import User
from . import schemas, service as crud

router = APIRouter()

@router.post("/", response_model=schemas.Mission, tags=["Missions"])
def create_mission(
    mission: schemas.MissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user)
):
    # Pass campaign_id from the current user
    return crud.create_mission(db=db, mission=mission, campaign_id=current_user.campaign_id)

@router.get("/", response_model=List[schemas.Mission], tags=["Missions"])
def read_missions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Filter by user's campaign
    missions = crud.get_missions(db, skip=skip, limit=limit, campaign_id=current_user.campaign_id)
    return missions

@router.get("/{mission_id}", response_model=schemas.Mission, tags=["Missions"])
def read_mission(
    mission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_mission = crud.get_mission(db, mission_id=mission_id)
    if db_mission is None:
        raise HTTPException(status_code=404, detail="Mission not found")

    # Ensure mission belongs to user's campaign
    if db_mission.campaign_id != current_user.campaign_id:
        raise HTTPException(status_code=404, detail="Mission not found")

    return db_mission

@router.post("/{mission_id}/signup", response_model=schemas.Mission, tags=["Missions"])
def signup_for_mission(
    mission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    mission = crud.get_mission(db, mission_id=mission_id)
    if not mission or mission.campaign_id != current_user.campaign_id:
        raise HTTPException(status_code=404, detail="Mission not found")

    character = current_user.character
    if not character:
        raise HTTPException(status_code=400, detail="User has no character to sign up with")

    if character in mission.players:
        raise HTTPException(status_code=400, detail="Character already signed up for this mission")

    return crud.add_character_to_mission(db, mission=mission, character=character)

@router.put("/{mission_id}/status", response_model=schemas.Mission, tags=["Missions"])
def update_mission_status(
    mission_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user)
):
    mission = crud.get_mission(db, mission_id=mission_id)
    if not mission or mission.campaign_id != current_user.campaign_id:
        raise HTTPException(status_code=404, detail="Mission not found")
    return crud.update_mission_status(db, mission=mission, status=status)

@router.post("/{mission_id}/distribute_rewards", tags=["Missions"])
def distribute_rewards(
    mission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user)
):
    mission = crud.get_mission(db, mission_id=mission_id)
    if not mission or mission.campaign_id != current_user.campaign_id:
        raise HTTPException(status_code=404, detail="Mission not found")

    result = crud.distribute_mission_rewards(db, mission=mission)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result
