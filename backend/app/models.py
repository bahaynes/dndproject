from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Table, DateTime
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="player", nullable=False)  # Roles: 'player', 'admin'
    is_active = Column(Boolean, default=True)

    character = relationship("Character", back_populates="owner", uselist=False)


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


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)

    inventory_items = relationship("InventoryItem", back_populates="item")
    store_listing = relationship("StoreItem", back_populates="item", uselist=False)


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    quantity = Column(Integer, default=1, nullable=False)

    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)

    character = relationship("Character", back_populates="inventory")
    item = relationship("Item", back_populates="inventory_items")


class StoreItem(Base):
    __tablename__ = "store_items"

    id = Column(Integer, primary_key=True, index=True)
    price = Column(Integer, nullable=False)
    # -1 for infinite quantity
    quantity_available = Column(Integer, default=-1, nullable=False)

    item_id = Column(Integer, ForeignKey("items.id"), unique=True)
    item = relationship("Item", back_populates="store_listing")


mission_players = Table('mission_players', Base.metadata,
    Column('mission_id', Integer, ForeignKey('missions.id'), primary_key=True),
    Column('character_id', Integer, ForeignKey('characters.id'), primary_key=True)
)

class Mission(Base):
    __tablename__ = "missions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, default="Available", nullable=False) # e.g., Available, In-Progress, Completed

    rewards = relationship("MissionReward", back_populates="mission", cascade="all, delete-orphan")
    players = relationship("Character", secondary=mission_players, back_populates="missions")


class MissionReward(Base):
    __tablename__ = "mission_rewards"

    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=False)

    item_id = Column(Integer, ForeignKey("items.id"), nullable=True)
    item = relationship("Item")

    xp = Column(Integer, nullable=True)
    scrip = Column(Integer, nullable=True)

    mission = relationship("Mission", back_populates="rewards")


game_session_players = Table('game_session_players', Base.metadata,
    Column('session_id', Integer, ForeignKey('game_sessions.id'), primary_key=True),
    Column('character_id', Integer, ForeignKey('characters.id'), primary_key=True)
)

class GameSession(Base):
    __tablename__ = "game_sessions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    session_date = Column(DateTime, nullable=False)
    status = Column(String, default="Scheduled", nullable=False) # e.g., Scheduled, Completed
    after_action_report = Column(String, nullable=True)

    players = relationship("Character", secondary=game_session_players, back_populates="game_sessions")
