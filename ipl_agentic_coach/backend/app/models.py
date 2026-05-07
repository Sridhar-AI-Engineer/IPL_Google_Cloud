from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True)
    points = Column(Integer, default=0, nullable=False)

    decisions = relationship("Decision", back_populates="user", cascade="all, delete-orphan")


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    team_a = Column(String, nullable=False)
    team_b = Column(String, nullable=False)
    date = Column(String, nullable=False)
    status = Column(String, default="live", nullable=False)

    decisions = relationship("Decision", back_populates="match", cascade="all, delete-orphan")


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    ball_number = Column(Integer, nullable=False)
    field_placement = Column(String, nullable=False)
    bowling_change = Column(String, nullable=False)
    tactical_strategy = Column(String, default="", nullable=False)
    timestamp = Column(String, nullable=False)
    score = Column(Float, default=0.0, nullable=False)
    feedback = Column(String, default="", nullable=False)

    user = relationship("User", back_populates="decisions")
    match = relationship("Match", back_populates="decisions")


class HistoricalDecision(Base):
    __tablename__ = "historical_decisions"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, nullable=False)
    ball_number = Column(Integer, nullable=False)
    field_placement = Column(String, nullable=False)
    bowler = Column(String, nullable=False)
    captain_move = Column(String, nullable=False)
    situation = Column(String, default="balanced", nullable=False)
    expected_score = Column(Float, default=0.6, nullable=False)