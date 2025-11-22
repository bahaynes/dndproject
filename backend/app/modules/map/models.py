from sqlalchemy import Column, Integer, String, Boolean, UniqueConstraint, Text
from ...database import Base

class MapTile(Base):
    __tablename__ = "map_tiles"

    id = Column(Integer, primary_key=True, index=True)
    q = Column(Integer, nullable=False)
    r = Column(Integer, nullable=False)
    terrain = Column(String, nullable=False, default="plains")
    is_revealed = Column(Boolean, default=False)
    description = Column(Text, nullable=True) # Visible to players if revealed
    notes = Column(Text, nullable=True) # DM internal notes

    __table_args__ = (
        UniqueConstraint('q', 'r', name='_q_r_uc'),
    )
