from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from ...database import Base

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

    # Scoping
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    campaign = relationship("Campaign", back_populates="missions")

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
