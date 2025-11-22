from uuid import uuid4

from sqlalchemy import Column, Integer, String, ForeignKey, Table, JSON
from sqlalchemy.orm import relationship

from ...database import Base

mission_players = Table(
    "mission_players",
    Base.metadata,
    Column("mission_id", String, ForeignKey("missions.id"), primary_key=True),
    Column("character_id", Integer, ForeignKey("characters.id"), primary_key=True),
)

class Mission(Base):
    __tablename__ = "missions"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    title = Column(String, index=True, nullable=False)
    summary = Column(String, nullable=True)
    status = Column(String, default="available", nullable=False)  # e.g., available, in_progress, completed
    target_hex = Column(String, ForeignKey("hex_defs.coordinate"), nullable=True)
    dossier_data = Column(JSON, default=dict)

    players = relationship("Character", secondary=mission_players, back_populates="missions")
