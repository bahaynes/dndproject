from sqlalchemy.orm import Session
from . import models, schemas
from ..characters import models as char_models

def get_game_session(db: Session, session_id: int):
    return db.query(models.GameSession).filter(models.GameSession.id == session_id).first()

def get_game_sessions(db: Session, campaign_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.GameSession).filter(
        models.GameSession.campaign_id == campaign_id
    ).offset(skip).limit(limit).all()

def create_game_session(db: Session, session: schemas.GameSessionCreate, campaign_id: int):
    db_session = models.GameSession(**session.model_dump(), campaign_id=campaign_id)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def add_character_to_game_session(db: Session, session: models.GameSession, character: char_models.Character):
    session.players.append(character)
    db.commit()
    db.refresh(session)
    return session

def remove_character_from_game_session(db: Session, session: models.GameSession, character: char_models.Character):
    session.players.remove(character)
    db.commit()
    db.refresh(session)
    return session

def update_game_session(db: Session, session: models.GameSession, session_update: schemas.GameSessionCreate):
    update_data = session_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(session, key, value)
    db.commit()
    db.refresh(session)
    return session

def create_session_proposal(db: Session, session_id: int, mission_id: int, user_id: int):
    db_proposal = models.SessionProposal(
        session_id=session_id,
        mission_id=mission_id,
        proposed_by_id=user_id
    )
    db.add(db_proposal)
    db.commit()
    db.refresh(db_proposal)
    return db_proposal

def get_session_proposal(db: Session, proposal_id: int):
    return db.query(models.SessionProposal).filter(models.SessionProposal.id == proposal_id).first()

def toggle_back_proposal(db: Session, proposal_id: int, character: char_models.Character):
    db_proposal = get_session_proposal(db, proposal_id)
    if not db_proposal:
        return None, "Proposal not found"

    session = db_proposal.session
    if session.status == "Confirmed":
        return None, "Session is already confirmed"

    if character in db_proposal.backers:
        db_proposal.backers.remove(character)
        db.commit()
        db.refresh(db_proposal)
        return db_proposal, None

    # Exclusion check: Can't back multiple proposals in same session
    existing_backing = db.query(models.SessionProposal).filter(
        models.SessionProposal.session_id == session.id,
        models.SessionProposal.backers.contains(character)
    ).first()

    if existing_backing:
        return None, "Already backed a proposal for this session"

    db_proposal.backers.append(character)
    db.commit()
    db.refresh(db_proposal)

    # Critical Mass Check
    if len(db_proposal.backers) >= session.min_players:
        confirm_session_proposal(db, db_proposal)

    return db_proposal, None

def confirm_session_proposal(db: Session, proposal: models.SessionProposal):
    session = proposal.session
    session.status = "Confirmed"
    session.confirmed_mission_id = proposal.mission_id
    proposal.status = "confirmed"

    # Dismiss others
    for other in session.proposals:
        if other.id != proposal.id:
            other.status = "dismissed"

    # Add all backers to session players
    session.players = list(proposal.backers)

    db.commit()
    db.refresh(session)
    return session

def force_confirm_proposal(db: Session, proposal_id: int):
    db_proposal = get_session_proposal(db, proposal_id)
    if not db_proposal:
        return None, "Proposal not found"

    return confirm_session_proposal(db, db_proposal), None

def veto_proposal(db: Session, proposal_id: int):
    db_proposal = get_session_proposal(db, proposal_id)
    if not db_proposal:
        return None, "Proposal not found"

    db_proposal.status = "vetoed"
    db.commit()
    db.refresh(db_proposal)
    return db_proposal, None

def remove_character_from_session(db: Session, session_id: int, character_id: int):
    session = get_game_session(db, session_id)
    if not session:
        return None, "Session not found"

    character = db.query(char_models.Character).filter(char_models.Character.id == character_id).first()
    if not character:
        return None, "Character not found"

    if character in session.players:
        session.players.remove(character)

    # Also remove from proposal backers if applicable
    for proposal in session.proposals:
        if character in proposal.backers:
            proposal.backers.remove(character)

    db.commit()
    db.refresh(session)
    return session, None
