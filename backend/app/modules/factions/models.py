from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from ...database import Base


class FactionReputation(Base):
    __tablename__ = "faction_reputations"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    faction_name = Column(String, nullable=False)
    level = Column(Integer, default=0, nullable=False)  # -5 to +5
    color = Column(String, nullable=True)        # hex color e.g. "#3b82f6"
    description = Column(String, nullable=True)  # one-line flavor text

    __table_args__ = (
        CheckConstraint("level >= -5 AND level <= 5", name="reputation_level_range"),
    )

    campaign = relationship("Campaign")
    events = relationship(
        "FactionReputationEvent",
        back_populates="reputation",
        cascade="all, delete-orphan",
        order_by="FactionReputationEvent.created_at.desc()",
    )


class FactionReputationEvent(Base):
    __tablename__ = "faction_reputation_events"

    id = Column(Integer, primary_key=True, index=True)
    reputation_id = Column(Integer, ForeignKey("faction_reputations.id"), nullable=False)
    delta = Column(Integer, nullable=False)  # positive or negative change
    description = Column(String, nullable=False)
    session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    reputation = relationship("FactionReputation", back_populates="events")
    session = relationship("GameSession")
