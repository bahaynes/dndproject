from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from ...database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # Discord specific fields
    discord_id = Column(String, index=True, nullable=False)
    username = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)

    # Multi-tenancy: User is scoped to a campaign
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)

    # Role in this specific campaign ('admin' aka DM, 'player')
    role = Column(String, default="player", nullable=False)

    is_active = Column(Boolean, default=True)

    # Relationships
    campaign = relationship("Campaign", back_populates="users")
    campaign = relationship("Campaign", back_populates="users")
    
    # Active character for the current session context
    active_character_id = Column(Integer, ForeignKey("characters.id"), nullable=True)
    active_character = relationship("Character", foreign_keys=[active_character_id])
    
    # All characters owned by this user
    characters = relationship("Character", back_populates="owner", foreign_keys="Character.owner_id")
