from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from ...database import Base

class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    image_url = Column(String, nullable=True)

    owner_id = Column(Integer, ForeignKey("users.id"), unique=True)
    owner = relationship("User", back_populates="character")

    stats = relationship("CharacterStats", back_populates="character", uselist=False, cascade="all, delete-orphan")
    inventory = relationship("InventoryItem", back_populates="character", cascade="all, delete-orphan")
    missions = relationship("Mission", secondary="mission_players", back_populates="players")
    game_sessions = relationship("GameSession", secondary="game_session_players", back_populates="players")


class CharacterStats(Base):
    __tablename__ = "character_stats"

    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id"), unique=True)

    xp = Column(Integer, default=0)
    scrip = Column(Integer, default=0)

    character = relationship("Character", back_populates="stats")
