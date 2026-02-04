from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from ...database import Base

class HexMap(Base):
    __tablename__ = "hex_maps"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    name = Column(String, nullable=False)
    width = Column(Integer, default=20)
    height = Column(Integer, default=20)

    # Appearance
    hex_size = Column(Integer, default=60) # Size in pixels for frontend reference
    default_terrain = Column(String, default="plains")

    campaign = relationship("Campaign")
    hexes = relationship("Hex", back_populates="map", cascade="all, delete-orphan")


class Hex(Base):
    __tablename__ = "hexes"

    id = Column(Integer, primary_key=True, index=True)
    map_id = Column(Integer, ForeignKey("hex_maps.id"), nullable=False)

    # Axial Coordinates
    q = Column(Integer, nullable=False)
    r = Column(Integer, nullable=False)

    # Properties
    terrain = Column(String, default="plains")
    is_discovered = Column(Boolean, default=False)
    notes = Column(String, nullable=True) # DM Notes

    # Content
    linked_mission_id = Column(Integer, ForeignKey("missions.id"), nullable=True)
    linked_location_name = Column(String, nullable=True)

    # Relationships
    map = relationship("HexMap", back_populates="hexes")
    linked_mission = relationship("Mission")

    __table_args__ = (
        UniqueConstraint('map_id', 'q', 'r', name='unique_hex_coord'),
    )
