from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from ...database import Base


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=True)

    # Event type: MissionCompleted | MissionFailed | CharacterDeath | LevelUp |
    #             Purchase | RewardDistribution | AdminAdjustment | ShipAdjustment
    event_type = Column(String, nullable=False)
    description = Column(String, nullable=False)

    # Essence delta (positive = gained, negative = spent)
    essence_delta = Column(Integer, default=0, nullable=False)

    # Ship state snapshot at time of entry: {"level": 1, "essence": 42}
    ship_snapshot = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    campaign = relationship("Campaign")
    session = relationship("GameSession")
