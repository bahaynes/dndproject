from sqlalchemy.orm import Session
from ..ship import models as ship_models
from . import models, schemas


def level_for_xp(xp: int) -> int:
    """Return the D&D 5e character level (1-20) for a given XP total."""
    level = 1
    for idx, threshold in enumerate(models.DND5E_XP_THRESHOLDS):
        if xp >= threshold:
            level = idx + 1
        else:
            break
    return min(level, 20)


def award_xp_and_gold(
    db: Session,
    character: models.Character,
    gold_delta: int = 0,
    xp_delta: int = 0,
) -> int | None:
    """Award gold and XP to a character, auto-leveling up per D&D 5e rules.
    Returns the new level if the character leveled up, otherwise None.
    """
    if character.stats is None:
        character.stats = models.CharacterStats(character_id=character.id, gold=0, xp=0)
        db.add(character.stats)
        db.flush()

    if gold_delta:
        character.stats.gold = max(0, (character.stats.gold or 0) + gold_delta)
    if xp_delta:
        character.stats.xp = max(0, (character.stats.xp or 0) + xp_delta)
        new_level = level_for_xp(character.stats.xp)
        if new_level > (character.level or 1):
            character.level = new_level
            return new_level
    return None


def get_character(db: Session, character_id: int):
    return db.query(models.Character).filter(models.Character.id == character_id).first()


def update_character(
    db: Session,
    character_id: int,
    character: schemas.CharacterUpdate | schemas.CharacterCreate,
    allow_level_change: bool = True,
):
    db_character = get_character(db, character_id)
    if db_character:
        update_data = character.model_dump(exclude_unset=True)
        if not allow_level_change:
            update_data.pop("level", None)
        for key, value in update_data.items():
            setattr(db_character, key, value)
        db.commit()
        db.refresh(db_character)
    return db_character


def create_character(db: Session, character: schemas.CharacterCreate, owner_id: int, campaign_id: int):
    db_character = models.Character(
        **character.model_dump(),
        owner_id=owner_id,
        campaign_id=campaign_id
    )
    db.add(db_character)
    db.commit()
    db.refresh(db_character)

    # Add stats
    hub = db.query(ship_models.Ship).filter_by(campaign_id=campaign_id).first()
    db_stats = models.CharacterStats(
        character_id=db_character.id, gold=hub.starting_gold if hub else 0, xp=0
    )
    db.add(db_stats)
    db.commit()
    db.refresh(db_character)

    return db_character
