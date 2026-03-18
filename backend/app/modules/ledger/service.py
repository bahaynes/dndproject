from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List

from . import models, schemas


def create_entry(
    db: Session,
    campaign_id: int,
    event_type: str,
    description: str,
    essence_delta: int = 0,
    session_id: Optional[int] = None,
    ship_snapshot: Optional[dict] = None,
) -> models.LedgerEntry:
    entry = models.LedgerEntry(
        campaign_id=campaign_id,
        session_id=session_id,
        event_type=event_type,
        description=description,
        essence_delta=essence_delta,
        ship_snapshot=ship_snapshot,
    )
    db.add(entry)
    db.flush()
    return entry


def get_entries(
    db: Session,
    campaign_id: int,
    event_type: Optional[str] = None,
    session_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[models.LedgerEntry]:
    q = db.query(models.LedgerEntry).filter(models.LedgerEntry.campaign_id == campaign_id)
    if event_type:
        q = q.filter(models.LedgerEntry.event_type == event_type)
    if session_id:
        q = q.filter(models.LedgerEntry.session_id == session_id)
    return q.order_by(desc(models.LedgerEntry.created_at)).offset(offset).limit(limit).all()
