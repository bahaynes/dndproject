from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from ...dependencies import get_db, get_current_active_user, get_current_active_admin_user, get_current_user
from ..auth.schemas import User
from . import schemas, service as crud

router = APIRouter()

@router.post("/", response_model=schemas.GameSession, tags=["Game Sessions"])
def create_session(
    session: schemas.GameSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user)
):
    return crud.create_game_session(db=db, session=session, campaign_id=current_user.campaign_id)

@router.get("/", response_model=List[schemas.GameSession], tags=["Game Sessions"])
def read_sessions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sessions = crud.get_game_sessions(db, campaign_id=current_user.campaign_id, skip=skip, limit=limit)
    return sessions

@router.get("/{session_id}", response_model=schemas.GameSession, tags=["Game Sessions"])
def read_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_session = crud.get_game_session(db, session_id=session_id)
    if db_session is None:
        raise HTTPException(status_code=404, detail="Game session not found")

    if db_session.campaign_id != current_user.campaign_id:
        raise HTTPException(status_code=404, detail="Game session not found")

    return db_session

@router.post("/{session_id}/signup", response_model=schemas.GameSession, tags=["Game Sessions"])
def signup_for_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_session = crud.get_game_session(db, session_id=session_id)
    if not db_session or db_session.campaign_id != current_user.campaign_id:
        raise HTTPException(status_code=404, detail="Game session not found")

    character = current_user.character
    if not character:
        raise HTTPException(status_code=400, detail="User has no character to sign up with")

    if character in db_session.players:
        raise HTTPException(status_code=400, detail="Character already signed up for this session")

    return crud.add_character_to_game_session(db, session=db_session, character=character)

@router.delete("/{session_id}/signup", response_model=schemas.GameSession, tags=["Game Sessions"])
def cancel_signup(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_session = crud.get_game_session(db, session_id=session_id)
    if not db_session or db_session.campaign_id != current_user.campaign_id:
        raise HTTPException(status_code=404, detail="Game session not found")

    character = current_user.character
    if not character:
        raise HTTPException(status_code=400, detail="User has no character")

    if character not in db_session.players:
        raise HTTPException(status_code=400, detail="Character not signed up for this session")

    return crud.remove_character_from_game_session(db, session=db_session, character=character)

@router.put("/{session_id}", response_model=schemas.GameSession, tags=["Game Sessions"])
def update_session(
    session_id: int,
    session_update: schemas.GameSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user)
):
    db_session = crud.get_game_session(db, session_id=session_id)
    if not db_session or db_session.campaign_id != current_user.campaign_id:
        raise HTTPException(status_code=404, detail="Game session not found")
    return crud.update_game_session(db, session=db_session, session_update=session_update)
