from uuid import uuid4

from sqlalchemy import Column, String, Float, Enum as SAEnum, JSON, ForeignKey
from sqlalchemy.orm import relationship

from ...database import Base
from ..common.enums import HexOwnership, FogLevel


class TerrainDef(Base):
    __tablename__ = "terrain_defs"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, unique=True, nullable=False)
    travel_cost_mult = Column(Float, nullable=False, default=1.0)
    color_hex = Column(String, nullable=False)
    icon_ref = Column(String, nullable=True)

    hexes = relationship("HexDef", back_populates="terrain")


class HexDef(Base):
    __tablename__ = "hex_defs"

    coordinate = Column(String, primary_key=True, index=True)
    terrain_id = Column(String, ForeignKey("terrain_defs.id"), nullable=False)
    owner = Column(SAEnum(HexOwnership), nullable=False, default=HexOwnership.NEUTRAL)
    fog_level = Column(SAEnum(FogLevel), nullable=False, default=FogLevel.BLACK)
    dossier_data = Column(JSON, default=dict)

    terrain = relationship("TerrainDef", back_populates="hexes")
