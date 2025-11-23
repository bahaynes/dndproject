from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ...dependencies import get_db, get_current_active_user
from ..auth.schemas import User
from . import schemas, service as crud

router = APIRouter()


@router.get("/", response_model=List[schemas.Character])
def list_characters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all characters owned by the current user."""

    return crud.list_characters_for_user(db=db, owner_id=current_user.id)


@router.post("/", response_model=schemas.Character, status_code=status.HTTP_201_CREATED)
def create_character(
    character: schemas.CharacterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new character for the current user."""

    return crud.create_character(db=db, character=character, owner_id=current_user.id)


@router.get("/{character_id}", response_model=schemas.Character)
def read_character(character_id: int, db: Session = Depends(get_db)):
    """Fetch a character with stats, inventory, missions, and sessions."""

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
    """Update character profile and stats. Only owners or admins can update."""

    db_character = crud.get_character(db, character_id=character_id)
    if db_character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    # Authorization check: only owner or admin can edit
    if db_character.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to update this character")
    return crud.update_character(db=db, character_id=character_id, character=character)
