from sqlalchemy.orm import Session
from datetime import datetime, timezone
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
    if session.status in ("Completed", "Cancelled"):
        return None, f"Cannot join a {session.status.lower()} session"
    if character in session.players:
        return session, None
    if len(session.players) >= session.max_players:
        return None, f"Session is full ({session.max_players}/{session.max_players} players)"
    session.players.append(character)
    db.commit()
    db.refresh(session)
    return session, None


def remove_character_from_game_session(db: Session, session: models.GameSession, character: char_models.Character):
    if character in session.players:
        session.players.remove(character)
        db.commit()
        db.refresh(session)
    return session


def cancel_game_session(db: Session, session: models.GameSession):
    if session.status == "Completed":
        return None, "Cannot cancel a completed session"
    session.status = "Cancelled"
    db.commit()
    db.refresh(session)
    return session, None

def update_field_report(db: Session, session: models.GameSession, field_report: str):
    session.field_report = field_report
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

def create_session_proposal(
    db: Session,
    session_id: int,
    user_id: int,
    mission_id: int | None = None,
    hex_id: int | None = None,
):
    db_proposal = models.SessionProposal(
        session_id=session_id,
        mission_id=mission_id,
        hex_id=hex_id,
        proposed_by_id=user_id,
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
    if session.status in ("Completed", "Cancelled"):
        return None, f"Cannot vote on a {session.status.lower()} session"
    if character not in session.players:
        return None, "Join the session before voting on a quest or hex"

    if character in db_proposal.backers:
        db_proposal.backers.remove(character)
        db.commit()
        db.refresh(db_proposal)
        return db_proposal, None

    # Move vote from any previously backed proposal in this session (1-click switch)
    for other in session.proposals:
        if other.id != db_proposal.id and character in other.backers:
            other.backers.remove(character)

    db_proposal.backers.append(character)
    db.commit()
    db.refresh(db_proposal)
    return db_proposal, None

def swap_character_in_session(
    db: Session,
    session: models.GameSession,
    owner_id: int,
    new_character: char_models.Character,
):
    if session.status in ("Completed", "Cancelled"):
        return None, f"Cannot swap character on a {session.status.lower()} session"
    if new_character.owner_id != owner_id:
        return None, "Character not owned by you"
    if new_character.status != "Active":
        return None, "Only Active characters can join a session"

    old_chars = [c for c in session.players if c.owner_id == owner_id]
    if not old_chars:
        return None, "You are not signed up for this session"

    for old in old_chars:
        if old.id == new_character.id:
            return session, None
        session.players.remove(old)
        for proposal in session.proposals:
            if old in proposal.backers:
                proposal.backers.remove(old)
                if new_character not in proposal.backers:
                    proposal.backers.append(new_character)

    if new_character not in session.players:
        session.players.append(new_character)

    db.commit()
    db.refresh(session)
    return session, None

def confirm_session_proposal(db: Session, proposal: models.SessionProposal):
    session = proposal.session
    session.status = "Confirmed"
    session.confirmed_mission_id = proposal.mission_id
    session.confirmed_hex_id = proposal.hex_id
    proposal.status = "confirmed"

    for other in session.proposals:
        if other.id != proposal.id:
            other.status = "dismissed"

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

def complete_session(
    db: Session,
    session: models.GameSession,
    data: schemas.SessionCompleteRequest,
    campaign_id: int,
):
    """
    Mark session Completed, record result, distribute rewards, adjust ship,
    create ledger entry, and handle casualties.
    """
    from ..missions import service as mission_service
    from ..ship import service as ship_service
    from ..characters import service as char_service
    from ..ledger.models import LedgerEntry

    if session.status == "Completed":
        return None, "Session is already completed"
    if data.result not in ("success", "failure"):
        return None, "result must be 'success' or 'failure'"

    if data.mission_id is not None:
        session.confirmed_mission_id = data.mission_id
    if data.hex_id is not None:
        session.confirmed_hex_id = data.hex_id

    session.status = "Completed"
    session.result = data.result
    session.essence_earned = data.essence_earned
    if data.after_action_report:
        session.after_action_report = data.after_action_report

    # Distribute mission rewards (gold + xp + items) on success
    if data.result == "success" and session.confirmed_mission_id:
        mission = mission_service.get_mission(db, session.confirmed_mission_id, campaign_id=campaign_id)
        if mission:
            mission.status = "Completed"
            mission.players = list(session.players)
            db.flush()

            mission_service.distribute_mission_rewards(db, mission)

            # Increment missions_completed for participants
            for character in session.players:
                character.missions_completed = (character.missions_completed or 0) + 1

    # Distribute session-level gold & XP (if specified)
    if data.gold_earned or data.xp_earned:
        for character in session.players:
            new_level = char_service.award_xp_and_gold(
                db, character, gold_delta=data.gold_earned, xp_delta=data.xp_earned
            )
            if new_level is not None:
                db.add(LedgerEntry(
                    campaign_id=campaign_id,
                    session_id=session.id,
                    event_type="LevelUp",
                    description=f"{character.name} reached Level {new_level} ({character.stats.xp} XP)",
                    essence_delta=0,
                ))

    # Handle casualties
    if data.casualties:
        casualty_chars = db.query(char_models.Character).filter(
            char_models.Character.id.in_(data.casualties),
            char_models.Character.campaign_id == campaign_id,
        ).all()
        for char in casualty_chars:
            char.status = "Dead"
            if char.date_of_death is None:
                char.date_of_death = datetime.now(timezone.utc)

    db.flush()

    # Auto-create ledger entry (and update treasury/ship if essence_earned != 0)
    event_type = "MissionCompleted" if data.result == "success" else "MissionFailed"
    mission_name = session.confirmed_mission.name if session.confirmed_mission else session.name
    reward_parts = []
    if data.gold_earned:
        reward_parts.append(f"+{data.gold_earned} GP")
    if data.xp_earned:
        reward_parts.append(f"+{data.xp_earned} XP")
    reward_suffix = f" ({', '.join(reward_parts)} per player)" if reward_parts else ""
    description = f"{event_type}: {mission_name}{reward_suffix}"

    ship_service.adjust_resources(
        db,
        campaign_id=campaign_id,
        description=description,
        essence_delta=data.essence_earned,
        session_id=session.id,
        event_type=event_type,
    )

    db.commit()
    db.refresh(session)
    return session, None


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
