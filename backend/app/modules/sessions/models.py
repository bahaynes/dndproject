from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime
from sqlalchemy.orm import relationship
from ...database import Base

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

    # Scoping
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    campaign = relationship("Campaign", back_populates="sessions")

    players = relationship("Character", secondary=game_session_players, back_populates="game_sessions")
