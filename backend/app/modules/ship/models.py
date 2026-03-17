from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from ...database import Base


class Ship(Base):
    __tablename__ = "ships"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False, unique=True)

    name = Column(String, nullable=False, default="The Ship")
    level = Column(Integer, default=1, nullable=False)

    fuel = Column(Integer, default=100, nullable=False)
    max_fuel = Column(Integer, default=100, nullable=False)
    crystals = Column(Integer, default=0, nullable=False)
    credits = Column(Integer, default=0, nullable=False)

    motd = Column(String, nullable=True)  # Message of the day / GM announcement

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    campaign = relationship("Campaign")

    @property
    def status(self) -> str:
        if self.max_fuel == 0:
            return "nominal"
        pct = self.fuel / self.max_fuel
        if pct < 0.25:
            return "critical"
        if pct < 0.50:
            return "low_fuel"
        return "nominal"
