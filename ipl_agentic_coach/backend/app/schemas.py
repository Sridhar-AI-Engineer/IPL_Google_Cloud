from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None


class UserEnsure(BaseModel):
    username: str
    email: Optional[str] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: Optional[str] = None
    points: int


class LeaderboardEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    points: int


class MatchCreate(BaseModel):
    team_a: str
    team_b: str
    date: str
    status: str = "live"


class MatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_a: str
    team_b: str
    date: str
    status: str


class DecisionCreate(BaseModel):
    user_id: int
    match_id: int
    ball_number: int
    field_placement: str
    bowling_change: str
    tactical_strategy: str = ""


class DecisionEvaluate(BaseModel):
    field_input: str
    bowler_input: str
    strategy_input: str = ""
    ball_number: int = 1


class DecisionSubmit(BaseModel):
    username: str
    field_input: str
    bowler_input: str
    strategy_input: str = ""
    ball_number: int = 1


class DecisionResult(BaseModel):
    score: float
    feedback: str
    historical_score: float
    simulation_impact: dict
    normalized_move: dict


class DecisionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    match_id: int
    ball_number: int
    field_placement: str
    bowling_change: str
    tactical_strategy: str
    score: float
    feedback: str
    timestamp: str


class DecisionSubmitResponse(BaseModel):
    decision: DecisionOut
    evaluation: DecisionResult
    leaderboard: list[LeaderboardEntry]