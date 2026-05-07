from datetime import datetime

from sqlalchemy.orm import Session

from . import models, schemas


def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(username=user.username, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def ensure_user(db: Session, user: schemas.UserEnsure):
    existing = get_user_by_username(db, user.username)
    if existing:
        if user.email and not existing.email:
            existing.email = user.email
            db.commit()
            db.refresh(existing)
        return existing

    return create_user(db, schemas.UserCreate(username=user.username, email=user.email))


def get_all_users(db: Session):
    return db.query(models.User).all()


def get_leaderboard(db: Session, limit: int = 10):
    return (
        db.query(models.User)
        .order_by(models.User.points.desc(), models.User.username.asc())
        .limit(limit)
        .all()
    )


def create_match(db: Session, match: schemas.MatchCreate):
    db_match = models.Match(
        team_a=match.team_a,
        team_b=match.team_b,
        date=match.date,
        status=match.status,
    )
    db.add(db_match)
    db.commit()
    db.refresh(db_match)
    return db_match


def get_match(db: Session, match_id: int):
    return db.query(models.Match).filter(models.Match.id == match_id).first()


def get_matches(db: Session):
    return db.query(models.Match).order_by(models.Match.id.desc()).all()


def get_current_match(db: Session):
    live_match = (
        db.query(models.Match)
        .filter(models.Match.status == "live")
        .order_by(models.Match.id.desc())
        .first()
    )
    if live_match:
        return live_match
    return db.query(models.Match).order_by(models.Match.id.desc()).first()


def ensure_default_match(db: Session):
    existing = get_current_match(db)
    if existing:
        return existing

    return create_match(
        db,
        schemas.MatchCreate(
            team_a="RCB",
            team_b="CSK",
            date=datetime.utcnow().strftime("%Y-%m-%d"),
            status="live",
        ),
    )


def create_decision(
    db: Session,
    decision: schemas.DecisionCreate,
    score: float = 0.0,
    feedback: str = "",
):
    db_decision = models.Decision(
        user_id=decision.user_id,
        match_id=decision.match_id,
        ball_number=decision.ball_number,
        field_placement=decision.field_placement,
        bowling_change=decision.bowling_change,
        tactical_strategy=decision.tactical_strategy,
        timestamp=datetime.utcnow().isoformat(timespec="seconds"),
        score=score,
        feedback=feedback,
    )
    db.add(db_decision)
    db.commit()
    db.refresh(db_decision)
    return db_decision

def get_decisions_by_match(db: Session, match_id: int):
    return (
        db.query(models.Decision)
        .filter(models.Decision.match_id == match_id)
        .order_by(models.Decision.id.desc())
        .all()
    )


def get_decisions_by_user(db: Session, user_id: int, limit: int = 50):
    safe_limit = min(max(limit, 1), 200)
    return (
        db.query(models.Decision)
        .filter(models.Decision.user_id == user_id)
        .order_by(models.Decision.id.desc())
        .limit(safe_limit)
        .all()
    )


def add_user_points(db: Session, user_id: int, points_to_add: int):
    user = get_user(db, user_id)
    if not user:
        return None

    user.points = max(0, user.points + points_to_add)
    db.commit()
    db.refresh(user)
    return user


def seed_historical_decisions(db: Session):
    existing_count = db.query(models.HistoricalDecision).count()
    if existing_count > 0:
        return

    seeds = [
        models.HistoricalDecision(
            match_id=1,
            ball_number=18,
            field_placement="deep midwicket",
            bowler="spinner",
            captain_move="Bring spinner with boundary rider",
            situation="defensive",
            expected_score=0.72,
        ),
        models.HistoricalDecision(
            match_id=1,
            ball_number=19,
            field_placement="slip + point up",
            bowler="fast yorker",
            captain_move="Attack with yorker specialist",
            situation="aggressive",
            expected_score=0.78,
        ),
        models.HistoricalDecision(
            match_id=1,
            ball_number=20,
            field_placement="long on + long off",
            bowler="fast slower ball",
            captain_move="Protect straight boundary",
            situation="balanced",
            expected_score=0.68,
        ),
    ]
    db.add_all(seeds)
    db.commit()


def get_historical_reference(db: Session, match_id: int, ball_number: int):
    item = (
        db.query(models.HistoricalDecision)
        .filter(models.HistoricalDecision.match_id == match_id)
        .filter(models.HistoricalDecision.ball_number == ball_number)
        .first()
    )

    if item:
        return {
            "field_placement": item.field_placement,
            "bowler": item.bowler,
            "captain_move": item.captain_move,
            "situation": item.situation,
            "expected_score": item.expected_score,
        }

    fallback = db.query(models.HistoricalDecision).order_by(models.HistoricalDecision.id.asc()).first()
    if fallback:
        return {
            "field_placement": fallback.field_placement,
            "bowler": fallback.bowler,
            "captain_move": fallback.captain_move,
            "situation": fallback.situation,
            "expected_score": fallback.expected_score,
        }

    return {
        "field_placement": "deep midwicket",
        "bowler": "spinner",
        "captain_move": "Default tactical reference",
        "situation": "balanced",
        "expected_score": 0.65,
    }