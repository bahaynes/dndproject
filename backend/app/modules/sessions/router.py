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

@router.get("/", response_model=List[schemas.GameSessionWithPlayers], tags=["Game Sessions"])
def read_sessions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sessions = crud.get_game_sessions(db, campaign_id=current_user.campaign_id, skip=skip, limit=limit)
    return sessions

@router.get("/{session_id}", response_model=schemas.GameSessionWithPlayers, tags=["Game Sessions"])
def read_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_session = crud.get_game_session(db, session_id=session_id)
    if db_session is None or db_session.campaign_id != current_user.campaign_id:
        raise HTTPException(status_code=404, detail="Game session not found")

    return db_session

@router.post("/proposals", response_model=schemas.SessionProposal, tags=["Game Sessions"])
def propose_mission(
    proposal: schemas.SessionProposalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_session = crud.get_game_session(db, session_id=proposal.session_id)
    if not db_session or db_session.campaign_id != current_user.campaign_id:
        raise HTTPException(status_code=404, detail="Game session not found")
    
    if db_session.status == "Confirmed":
        raise HTTPException(status_code=400, detail="Cannot propose for a confirmed session")

    return crud.create_session_proposal(
        db, 
        session_id=proposal.session_id, 
        mission_id=proposal.mission_id, 
        user_id=current_user.id
    )

@router.post("/proposals/{proposal_id}/toggle_back", response_model=schemas.SessionProposal, tags=["Game Sessions"])
def toggle_backing(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    character = current_user.character
    if not character:
        raise HTTPException(status_code=400, detail="User has no character")

    db_proposal, error = crud.toggle_back_proposal(db, proposal_id=proposal_id, character=character)
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return db_proposal

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

@router.post("/proposals/{proposal_id}/force_confirm", response_model=schemas.GameSessionWithPlayers, tags=["Admin"])
def force_confirm(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user)
):
    session, error = crud.force_confirm_proposal(db, proposal_id=proposal_id)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return session

@router.post("/proposals/{proposal_id}/veto", response_model=schemas.SessionProposal, tags=["Admin"])
def veto_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user)
):
    proposal, error = crud.veto_proposal(db, proposal_id=proposal_id)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return proposal

@router.delete("/{session_id}/kick/{character_id}", response_model=schemas.GameSessionWithPlayers, tags=["Admin"])
def kick_player(
    session_id: int,
    character_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user)
):
    session, error = crud.remove_character_from_session(db, session_id=session_id, character_id=character_id)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return session
