from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from ...dependencies import get_db, get_current_active_admin_user
from . import schemas, service as crud

router = APIRouter()


@router.post(
    "/",
    response_model=schemas.Mission,
    tags=["Missions"],
    dependencies=[Depends(get_current_active_admin_user)],
)
def create_mission(mission: schemas.MissionCreate, db: Session = Depends(get_db)):
    """Create a mission with target hex and dossier (admin/GM)."""

    return crud.create_mission(db=db, mission=mission)


@router.get("/", response_model=List[schemas.Mission], tags=["Missions"])
def read_missions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List missions available for scheduling."""

    missions = crud.get_missions(db, skip=skip, limit=limit)
    return missions


@router.get("/{mission_id}", response_model=schemas.Mission, tags=["Missions"])
def read_mission(mission_id: str, db: Session = Depends(get_db)):
    """Fetch a mission and its dossier."""

    db_mission = crud.get_mission(db, mission_id=mission_id)
    if db_mission is None:
        raise HTTPException(status_code=404, detail="Mission not found")
    return db_mission


@router.put(
    "/{mission_id}",
    response_model=schemas.Mission,
    tags=["Missions"],
    dependencies=[Depends(get_current_active_admin_user)],
)
def update_mission(mission_id: str, mission_in: schemas.MissionCreate, db: Session = Depends(get_db)):
    """Update mission metadata and dossier (admin/GM)."""

    mission = crud.get_mission(db, mission_id=mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return crud.update_mission(db, mission=mission, mission_in=mission_in)
