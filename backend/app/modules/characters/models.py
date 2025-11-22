from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SAEnum, Boolean
from sqlalchemy.orm import relationship
from ...database import Base
from ..common.enums import CharacterStatus

class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    image_url = Column(String, nullable=True)

    status = Column(
        SAEnum(
            CharacterStatus,
            name="characterstatus",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        default=CharacterStatus.READY.value,
        nullable=False,
    )

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="characters")

    stats = relationship("CharacterStats", back_populates="character", uselist=False, cascade="all, delete-orphan")
    inventory = relationship("InventoryItem", back_populates="character", cascade="all, delete-orphan")
    missions = relationship("Mission", secondary="mission_players", back_populates="players")
    game_sessions = relationship("GameSession", secondary="game_session_players", back_populates="players")


class CharacterStats(Base):
    __tablename__ = "character_stats"

    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id"), unique=True)

    xp = Column(Integer, default=0, nullable=False)
    commendations = Column(Integer, default=0, nullable=False)
    current_hp = Column(Integer, default=0, nullable=False)
    short_rest_available = Column(Boolean, default=True, nullable=False)

    character = relationship("Character", back_populates="stats")
