from sqlalchemy.orm import Session

from . import models, schemas


def list_terrain(db: Session):
    return db.query(models.TerrainDef).order_by(models.TerrainDef.name).all()


def create_terrain(db: Session, terrain: schemas.TerrainDefCreate):
    terrain_obj = models.TerrainDef(**terrain.model_dump())
    db.add(terrain_obj)
    db.commit()
    db.refresh(terrain_obj)
    return terrain_obj


def update_terrain(db: Session, terrain_id: str, terrain: schemas.TerrainDefCreate):
    db_terrain = db.query(models.TerrainDef).filter(models.TerrainDef.id == terrain_id).first()
    if not db_terrain:
        return None
    for key, value in terrain.model_dump(exclude_unset=True).items():
        setattr(db_terrain, key, value)
    db.commit()
    db.refresh(db_terrain)
    return db_terrain


def list_hexes(db: Session):
    return db.query(models.HexDef).order_by(models.HexDef.coordinate).all()


def upsert_hex(db: Session, hex_in: schemas.HexDefCreate):
    db_hex = db.query(models.HexDef).filter(models.HexDef.coordinate == hex_in.coordinate).first()
    if not db_hex:
        db_hex = models.HexDef(**hex_in.model_dump())
        db.add(db_hex)
    else:
        for key, value in hex_in.model_dump(exclude_unset=True).items():
            setattr(db_hex, key, value)
    db.commit()
    db.refresh(db_hex)
    return db_hex
