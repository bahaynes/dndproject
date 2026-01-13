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
    character = relationship("Character", back_populates="owner", uselist=False)
