from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from ...database import Base

LEVEL_THRESHOLDS = [0, 5, 10, 15, 20, 36, 52, 68, 84, 100, 116, 156, 196, 236, 276, 316, 356, 496, 636, 776]


class Ship(Base):
    __tablename__ = "ships"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False, unique=True)

    name = Column(String, nullable=False, default="The Ship")
    level = Column(Integer, default=1, nullable=False)
    essence = Column(Integer, default=0, nullable=False)

    motd = Column(String, nullable=True)  # Message of the day / GM announcement

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    campaign = relationship("Campaign")

    @property
    def long_rest_cost(self) -> int:
        if self.level >= 17:
            return 8
        if self.level >= 11:
            return 6
        if self.level >= 5:
            return 4
        return 2

    @property
    def next_threshold(self) -> int | None:
        # level is 1-indexed; next threshold is at LEVEL_THRESHOLDS[level]
        if self.level >= len(LEVEL_THRESHOLDS):
            return None
        return LEVEL_THRESHOLDS[self.level]

    @property
    def essence_to_next_level(self) -> int:
        if self.next_threshold is None:
            return 0
        return max(0, self.next_threshold - self.essence)

    @property
    def status(self) -> str:
        if self.essence == 0:
            return "critical"
        if self.essence < self.long_rest_cost:
            return "low"
        return "nominal"
