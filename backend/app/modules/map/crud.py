from sqlalchemy.orm import Session
from . import models, schemas

def get_tile(db: Session, tile_id: int):
    return db.query(models.MapTile).filter(models.MapTile.id == tile_id).first()

def get_tile_by_coords(db: Session, q: int, r: int):
    return db.query(models.MapTile).filter(models.MapTile.q == q, models.MapTile.r == r).first()

def get_tiles(db: Session, skip: int = 0, limit: int = 1000, revealed_only: bool = False):
    query = db.query(models.MapTile)
    if revealed_only:
        query = query.filter(models.MapTile.is_revealed == True)
    return query.offset(skip).limit(limit).all()

def create_tile(db: Session, tile: schemas.MapTileCreate):
    db_tile = models.MapTile(**tile.model_dump())
    db.add(db_tile)
    db.commit()
    db.refresh(db_tile)
    return db_tile

def update_tile(db: Session, tile_id: int, tile_update: schemas.MapTileUpdate):
    db_tile = get_tile(db, tile_id)
    if not db_tile:
        return None

    update_data = tile_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_tile, key, value)

    db.add(db_tile)
    db.commit()
    db.refresh(db_tile)
    return db_tile
