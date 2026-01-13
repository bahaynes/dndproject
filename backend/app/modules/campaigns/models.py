from sqlalchemy import Column, Integer, String, BigInteger
from sqlalchemy.orm import relationship

from ...database import Base

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    # Using BigInteger for Discord IDs (snowflake)
    discord_guild_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)

    # Role IDs for role-based access control within the campaign
    dm_role_id = Column(String, nullable=True)
    player_role_id = Column(String, nullable=True)

    # Relationships
    users = relationship("User", back_populates="campaign")
    characters = relationship("Character", back_populates="campaign")
    items = relationship("Item", back_populates="campaign")
    missions = relationship("Mission", back_populates="campaign")
    sessions = relationship("GameSession", back_populates="campaign")
