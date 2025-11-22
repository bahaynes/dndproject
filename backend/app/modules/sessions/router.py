from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from ...dependencies import get_db, get_current_active_user, get_current_active_admin_user
from ..auth.schemas import User
from ..characters import service as character_service
from . import schemas, service as crud

router = APIRouter()


@router.post(
    "/",
    response_model=schemas.GameSession,
    tags=["Game Sessions"],
    dependencies=[Depends(get_current_active_admin_user)],
)
def create_game_session(session: schemas.GameSessionCreate, db: Session = Depends(get_db)):
    """Create a session (Session Captain/GM flow)."""

    return crud.create_game_session(db=db, session=session)


@router.get("/", response_model=List[schemas.GameSession], tags=["Game Sessions"])
def read_game_sessions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List sessions for lobby views."""

    sessions = crud.get_game_sessions(db, skip=skip, limit=limit)
    return sessions


@router.get("/{session_id}", response_model=schemas.GameSession, tags=["Game Sessions"])
def read_game_session(session_id: str, db: Session = Depends(get_db)):
    """Fetch a single session with roster."""

    db_session = crud.get_game_session(db, session_id=session_id)
    if db_session is None:
        raise HTTPException(status_code=404, detail="Game session not found")
    return db_session


@router.put(
    "/{session_id}",
    response_model=schemas.GameSession,
    tags=["Game Sessions"],
    dependencies=[Depends(get_current_active_admin_user)],
)
def update_game_session(session_id: str, session_update: schemas.GameSessionCreate, db: Session = Depends(get_db)):
    """Update session metadata (admin/GM)."""

    session = crud.get_game_session(db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game session not found")
    return crud.update_game_session(db, session=session, session_update=session_update)


@router.post("/{session_id}/signup", response_model=schemas.GameSession, tags=["Game Sessions"])
def signup_for_session(
    session_id: str,
    signup: schemas.SessionSignupRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Sign a specific Ready character up for a session."""

    session = crud.get_game_session(db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game session not found")

    character = character_service.get_character(db, character_id=signup.character_id)
    if not character or character.owner_id != current_user.id:
        raise HTTPException(status_code=400, detail="Character not found for user")

    if character in session.players:
        raise HTTPException(status_code=400, detail="Character already signed up for this session")

    return crud.add_character_to_game_session(db, session=session, character=character)


@router.delete("/{session_id}/signup", response_model=schemas.GameSession, tags=["Game Sessions"])
def cancel_signup_for_session(
    session_id: str,
    signup: schemas.SessionSignupRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Remove a character signup from a session."""

    session = crud.get_game_session(db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game session not found")

    character = character_service.get_character(db, character_id=signup.character_id)
    if not character or character.owner_id != current_user.id:
        raise HTTPException(status_code=400, detail="Character not found for user")

    if character not in session.players:
        raise HTTPException(status_code=400, detail="Character is not signed up for this session")

    return crud.remove_character_from_game_session(db, session=session, character=character)
