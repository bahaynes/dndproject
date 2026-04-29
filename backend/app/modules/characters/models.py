from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from ...database import Base

class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    character_sheet_url = Column(String, nullable=True)
    ship_ability_notes = Column(String, nullable=True)

    class_name = Column(String, nullable=True)
    level = Column(Integer, default=1, nullable=False)
    status = Column(String, default="Active", nullable=False)  # Active | Dead | Benched
    date_of_death = Column(DateTime, nullable=True)
    missions_completed = Column(Integer, default=0, nullable=False)

    # Scoping
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    campaign = relationship("Campaign", back_populates="characters")

    owner_id = Column(Integer, ForeignKey("users.id"), unique=False, index=True)
    owner = relationship("User", back_populates="characters", foreign_keys=[owner_id])

    stats = relationship("CharacterStats", back_populates="character", uselist=False, cascade="all, delete-orphan")
    inventory = relationship("InventoryItem", back_populates="character", cascade="all, delete-orphan")
    missions = relationship("Mission", secondary="mission_players", back_populates="players")
    game_sessions = relationship("GameSession", secondary="game_session_players", back_populates="players")


class CharacterStats(Base):
    __tablename__ = "character_stats"

    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id"), unique=True)

    gold = Column(Integer, default=0)

    character = relationship("Character", back_populates="stats")
