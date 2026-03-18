from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ...dependencies import get_db, get_current_user, get_current_active_admin_user
from ..auth.schemas import User
from ..ship import service as ship_service
from . import schemas, service

router = APIRouter()


@router.get("/", response_model=List[schemas.LedgerEntryOut], tags=["Ledger"])
def get_ledger(
    event_type: Optional[str] = Query(None),
    session_id: Optional[int] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.get_entries(
        db,
        campaign_id=current_user.campaign_id,
        event_type=event_type,
        session_id=session_id,
        limit=limit,
        offset=offset,
    )


@router.post("/", response_model=schemas.LedgerEntryOut, tags=["Ledger"])
def create_ledger_entry(
    data: schemas.LedgerEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user),
):
    if data.event_type not in schemas.VALID_EVENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid event_type: {data.event_type}")

    ship = ship_service.get_or_create_ship(db, campaign_id=current_user.campaign_id)
    snapshot = ship_service.get_snapshot(ship)

    entry = service.create_entry(
        db=db,
        campaign_id=current_user.campaign_id,
        event_type=data.event_type,
        description=data.description,
        essence_delta=data.essence_delta,
        session_id=data.session_id,
        ship_snapshot=snapshot,
    )
    db.commit()
    db.refresh(entry)
    return entry
