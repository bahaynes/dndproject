from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ...dependencies import get_db, get_current_active_user
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
