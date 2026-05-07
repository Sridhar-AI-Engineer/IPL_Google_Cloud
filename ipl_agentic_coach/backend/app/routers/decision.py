from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas, database
from ..ai_service import tactical_ai_service
from ..firebase_auth import verify_firebase_token
from ..runtime_controls import build_cache_key, runtime_controls

router = APIRouter()


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=schemas.DecisionOut)
def create_decision(decision: schemas.DecisionCreate, db: Session = Depends(get_db)):
    user = crud.get_user(db, decision.user_id)
    match = crud.get_match(db, decision.match_id)
    if not user or not match:
        raise HTTPException(status_code=404, detail="User or Match not found")
    return crud.create_decision(db, decision)


@router.get("/match/{match_id}", response_model=list[schemas.DecisionOut])
def get_decisions(match_id: int, db: Session = Depends(get_db)):
    return crud.get_decisions_by_match(db, match_id)


@router.get("/history/{username}", response_model=list[schemas.DecisionOut])
def get_user_decision_history(username: str, limit: int = 30, db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, username)
    if not user:
        return []
    return crud.get_decisions_by_user(db, user.id, limit=limit)


MAX_USER_DECISIONS_PER_HOUR = 20
MAX_AI_CALLS_PER_DAY = 950
EVAL_CACHE_TTL = timedelta(minutes=10)


@router.post("/evaluate", response_model=schemas.DecisionResult)
def evaluate_decision(payload: schemas.DecisionEvaluate, db: Session = Depends(get_db)):
    match = crud.ensure_default_match(db)
    historical_move = crud.get_historical_reference(db, match.id, payload.ball_number)
    result = tactical_ai_service.evaluate_decision(
        payload.field_input,
        payload.bowler_input,
        payload.strategy_input,
        historical_move,
    )
    return result


@router.post("/submit", response_model=schemas.DecisionSubmitResponse)
def submit_decision(
    payload: schemas.DecisionSubmit,
    db: Session = Depends(get_db),
    firebase_user: dict = Depends(verify_firebase_token),
):
    user_key = payload.username.strip().lower()
    firebase_uid = str(firebase_user.get("uid", "")).strip()
    if firebase_uid:
        user_key = firebase_uid

    if not runtime_controls.check_user_rate_limit(
        user_key=user_key,
        max_events=MAX_USER_DECISIONS_PER_HOUR,
        window=timedelta(hours=1),
    ):
        raise HTTPException(status_code=429, detail="Rate limit reached. Try again in a few minutes.")

    user = crud.ensure_user(db, schemas.UserEnsure(username=payload.username, email=None))
    match = crud.ensure_default_match(db)
    historical_move = crud.get_historical_reference(db, match.id, payload.ball_number)

    cache_key = build_cache_key(
        match_id=match.id,
        ball_number=payload.ball_number,
        field_input=payload.field_input,
        bowler_input=payload.bowler_input,
        strategy_input=payload.strategy_input,
    )
    cached_eval = runtime_controls.get_cached_evaluation(cache_key=cache_key, ttl=EVAL_CACHE_TTL)

    if cached_eval is not None:
        evaluation = cached_eval
    else:
        if not runtime_controls.check_ai_quota(MAX_AI_CALLS_PER_DAY):
            raise HTTPException(status_code=429, detail="Daily AI quota reached. Please try again tomorrow.")

        evaluation = tactical_ai_service.evaluate_decision(
            payload.field_input,
            payload.bowler_input,
            payload.strategy_input,
            historical_move,
        )
        runtime_controls.consume_ai_quota()
        runtime_controls.set_cached_evaluation(cache_key=cache_key, payload=evaluation)

    runtime_controls.consume_user_rate_limit(user_key=user_key, window=timedelta(hours=1))

    decision_create = schemas.DecisionCreate(
        user_id=user.id,
        match_id=match.id,
        ball_number=payload.ball_number,
        field_placement=payload.field_input,
        bowling_change=payload.bowler_input,
        tactical_strategy=payload.strategy_input,
    )
    decision = crud.create_decision(
        db,
        decision_create,
        score=evaluation["score"],
        feedback=evaluation["feedback"],
    )

    points = max(1, int(round(evaluation["score"] * 100)))
    crud.add_user_points(db, user.id, points)

    leaderboard = crud.get_leaderboard(db, limit=10)
    return {
        "decision": decision,
        "evaluation": evaluation,
        "leaderboard": leaderboard,
    }