from uuid import uuid4

from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime, JSON, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
from ...database import Base
from ..common.enums import SessionStatus

game_session_players = Table(
    "game_session_players",
    Base.metadata,
    Column("session_id", String, ForeignKey("game_sessions.id"), primary_key=True),
    Column("character_id", Integer, ForeignKey("characters.id"), primary_key=True),
)


class GameSession(Base):
    __tablename__ = "game_sessions"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    mission_id = Column(String, ForeignKey("missions.id"), nullable=False)
    title = Column(String, index=True, nullable=False)
    session_date = Column(DateTime, nullable=False)
    status = Column(
        SAEnum(
            SessionStatus,
            name="sessionstatus",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        default=SessionStatus.OPEN.value,
        nullable=False,
    )
    route_data = Column(JSON, default=list)
    gm_notes = Column(Text, nullable=True)
    aar_summary = Column(Text, nullable=True)

    players = relationship("Character", secondary=game_session_players, back_populates="game_sessions")
    mission = relationship("Mission")
