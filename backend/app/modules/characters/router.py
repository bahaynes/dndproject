from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ...dependencies import get_db, get_current_active_user, get_current_active_admin_user
from ..auth.schemas import User
from . import schemas, service as crud, models

router = APIRouter()

@router.post("/", response_model=schemas.Character)
def create_character(
    character: schemas.CharacterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Remove restriction: Users can have multiple characters now
    
    new_char = crud.create_character(
        db=db, 
        character=character, 
        owner_id=current_user.id, 
        campaign_id=current_user.campaign_id
    )

    # If this is their first character, set it as active automatically
    if not current_user.active_character_id:
        current_user.active_character_id = new_char.id
        db.commit()
    
    return new_char

@router.get("/roster", response_model=List[schemas.CharacterRosterEntry], tags=["Characters"])
def get_crew_roster(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return all characters in the campaign (all players), optionally filtered by status."""
    from ..auth import models as auth_models
    q = (
        db.query(models.Character)
        .filter(models.Character.campaign_id == current_user.campaign_id)
    )
    if status_filter:
        q = q.filter(models.Character.status == status_filter)
    chars = q.all()
    # Attach owner username
    result = []
    for c in chars:
        owner = db.query(auth_models.User).filter(auth_models.User.id == c.owner_id).first()
        entry = schemas.CharacterRosterEntry(
            id=c.id,
            name=c.name,
            class_name=c.class_name,
            level=c.level,
            status=c.status,
            date_of_death=c.date_of_death,
            missions_completed=c.missions_completed,
            owner_id=c.owner_id,
            owner_username=owner.username if owner else None,
        )
        result.append(entry)
    return result


@router.get("/", response_model=List[schemas.Character])
def read_my_characters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return db.query(models.Character).filter(models.Character.owner_id == current_user.id).all()

@router.get("/{character_id}", response_model=schemas.Character)
def read_character(character_id: int, db: Session = Depends(get_db)):
    db_character = crud.get_character(db, character_id=character_id)
    if db_character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    return db_character


@router.put("/{character_id}", response_model=schemas.Character)
def update_character(
    character_id: int,
    character: schemas.CharacterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    db_character = crud.get_character(db, character_id=character_id)
    if db_character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    # Authorization check: only owner or admin can edit
    if db_character.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to update this character")
    return crud.update_character(db=db, character_id=character_id, character=character)

@router.post("/{character_id}/activate", response_model=User)
def activate_character(
    character_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_character = crud.get_character(db, character_id=character_id)
    if not db_character or db_character.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Character not found or not owned by you")
    
    current_user.active_character_id = db_character.id
    current_user.active_character = db_character
    db.commit()
    return current_user

@router.post("/{character_id}/status", response_model=schemas.Character)
def update_character_status(
    character_id: int,
    data: schemas.CharacterStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin_user),
):
    """Admin sets character status (Active / Dead / Benched)."""
    db_character = crud.get_character(db, character_id=character_id)
    if db_character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    if data.status not in ("Active", "Dead", "Benched"):
        raise HTTPException(status_code=400, detail="status must be Active, Dead, or Benched")
    db_character.status = data.status
    if data.status == "Dead" and db_character.date_of_death is None:
        db_character.date_of_death = datetime.utcnow()
    elif data.status != "Dead":
        db_character.date_of_death = None
    db.commit()
    db.refresh(db_character)
    return db_character


@router.delete("/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_character(
    character_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_character = crud.get_character(db, character_id=character_id)
    if not db_character:
        raise HTTPException(status_code=404, detail="Character not found")
        
    if db_character.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this character")
    
    # If deleting active character, unset active_character_id
    if current_user.active_character_id == character_id:
        current_user.active_character_id = None
        
    db.delete(db_character)
    db.commit()
