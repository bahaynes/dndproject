from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime
from sqlalchemy.orm import relationship
from ...database import Base

game_session_players = Table('game_session_players', Base.metadata,
    Column('session_id', Integer, ForeignKey('game_sessions.id'), primary_key=True),
    Column('character_id', Integer, ForeignKey('characters.id'), primary_key=True)
)

proposal_backers = Table('proposal_backers', Base.metadata,
    Column('proposal_id', Integer, ForeignKey('session_proposals.id'), primary_key=True),
    Column('character_id', Integer, ForeignKey('characters.id'), primary_key=True)
)

class GameSession(Base):
    __tablename__ = "game_sessions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    session_date = Column(DateTime, nullable=False)
    status = Column(String, default="Scheduled", nullable=False) # e.g., Open, Contested, Confirmed, Completed, Cancelled
    after_action_report = Column(String, nullable=True)
    
    min_players = Column(Integer, default=4)
    max_players = Column(Integer, default=6)
    
    confirmed_mission_id = Column(Integer, ForeignKey("missions.id"), nullable=True)
    confirmed_mission = relationship("Mission")

    # Scoping
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    campaign = relationship("Campaign", back_populates="sessions")

    players = relationship("Character", secondary=game_session_players, back_populates="game_sessions")
    proposals = relationship("SessionProposal", back_populates="session", cascade="all, delete-orphan")

class SessionProposal(Base):
    __tablename__ = "session_proposals"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("game_sessions.id"), nullable=False)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=False)
    proposed_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    status = Column(String, default="proposed") # e.g., proposed, confirmed, dismissed
    
    # Relationships
    session = relationship("GameSession", back_populates="proposals")
    mission = relationship("Mission")
    proposer = relationship("User")
    backers = relationship("Character", secondary=proposal_backers)
