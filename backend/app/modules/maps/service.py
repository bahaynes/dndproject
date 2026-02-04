from sqlalchemy.orm import Session
from . import models, schemas

def get_maps(db: Session, campaign_id: int):
    return db.query(models.HexMap).filter(models.HexMap.campaign_id == campaign_id).all()

def get_map(db: Session, map_id: int):
    return db.query(models.HexMap).filter(models.HexMap.id == map_id).first()

def create_map(db: Session, map_in: schemas.HexMapCreate, campaign_id: int, seed: bool = True):
    db_map = models.HexMap(**map_in.model_dump(), campaign_id=campaign_id)
    db.add(db_map)
    db.commit()
    db.refresh(db_map)

    if seed:
        seed_hex_grid(db, db_map.id)

    return db_map

def seed_hex_grid(db: Session, map_id: int, radius: int = 5):
    """Generates a starting hex grid for the map."""
    hexes = []
    types = ['plains', 'forest', 'mountain', 'water', 'desert', 'swamp']

    for q in range(-radius, radius + 1):
        r1 = max(-radius, -q - radius)
        r2 = min(radius, -q + radius)
        for r in range(r1, r2 + 1):
            # Deterministic terrain based on q,r for variety
            terrain_idx = abs(q + r * 3) % len(types)
            is_start = (q == 0 and r == 0)

            db_hex = models.Hex(
                map_id=map_id,
                q=q,
                r=r,
                terrain=types[terrain_idx],
                is_discovered=is_start, # Start with center discovered
                linked_location_name="Starting Camp" if is_start else None
            )
            db.add(db_hex)

    db.commit()

def get_hex(db: Session, map_id: int, q: int, r: int):
    return db.query(models.Hex).filter(
        models.Hex.map_id == map_id,
        models.Hex.q == q,
        models.Hex.r == r
    ).first()

def update_hex(db: Session, map_id: int, q: int, r: int, hex_update: schemas.HexUpdate):
    db_hex = get_hex(db, map_id, q, r)

    if not db_hex:
        # Create if doesn't exist (Upsert logic)
        db_hex = models.Hex(
            map_id=map_id,
            q=q,
            r=r,
            **hex_update.model_dump(exclude_unset=True)
        )
        db.add(db_hex)
    else:
        update_data = hex_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_hex, key, value)

    db.commit()
    db.refresh(db_hex)
    return db_hex

def bulk_update_hexes(db: Session, map_id: int, hexes: list[schemas.HexBase]):
    # Optimized implementation would use bulk_save_objects or raw SQL
    # For now, simple loop is safer
    updated = []
    for h in hexes:
        # Quick and dirty implementation reusing single update
        # In a real app with 1000s of hexes, this needs optimization
        update_schema = schemas.HexUpdate(**h.model_dump())
        updated.append(update_hex(db, map_id, h.q, h.r, update_schema))
    return updated
