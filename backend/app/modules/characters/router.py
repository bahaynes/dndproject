from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

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
    # Check if user already has a character in this campaign
    existing = db.query(models.Character).filter(models.Character.owner_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already has a character in this campaign")
    
    return crud.create_character(
        db=db, 
        character=character, 
        owner_id=current_user.id, 
        campaign_id=current_user.campaign_id
    )

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
