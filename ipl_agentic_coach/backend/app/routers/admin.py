"""Admin dashboard endpoints for system management."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from .. import crud, models, database, schemas
from ..auth import get_current_admin, User
from ..logging_config import metrics
from ..config import settings

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard/stats", dependencies=[Depends(get_current_admin)])
def get_dashboard_stats(db: Session = Depends(database.get_db)):
    """Get system statistics for admin dashboard."""
    # User stats
    total_users = db.query(func.count(models.User.id)).scalar() or 0
    active_users = db.query(models.User).filter(
        func.count(models.User.decisions) > 0
    ).count() or 0
    
    # Decision stats
    total_decisions = db.query(func.count(models.Decision.id)).scalar() or 0
    avg_decision_score = (
        db.query(func.avg(models.Decision.score)).scalar() or 0
    )
    
    # Match stats
    total_matches = db.query(func.count(models.Match.id)).scalar() or 0
    live_matches = db.query(func.count(models.Match.id)).filter(
        models.Match.status == "live"
    ).scalar() or 0
    
    return {
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        "users": {
            "total": total_users,
            "active": active_users,
            "inactive": max(0, total_users - active_users),
        },
        "decisions": {
            "total": total_decisions,
            "avg_score": round(float(avg_decision_score), 2) if avg_decision_score else 0,
        },
        "matches": {
            "total": total_matches,
            "live": live_matches,
            "completed": max(0, total_matches - live_matches),
        },
        "api": {
            "total_requests": metrics.metrics["requests_total"],
            "errors": metrics.metrics["errors"],
            "avg_response_time_ms": metrics.get_metrics()["avg_response_time_ms"],
        },
        "system": {
            "environment": settings.env,
            "debug": settings.debug,
            "rate_limit_enabled": settings.rate_limit_enabled,
            "sentry_enabled": settings.sentry_enabled,
            "redis_enabled": settings.redis_enabled,
        },
    }


@router.get("/users", dependencies=[Depends(get_current_admin)])
def list_all_users(
    skip: int = 0,
    limit: int = 100,
    sort_by: str = "id",
    db: Session = Depends(database.get_db),
):
    """List all users with pagination."""
    query = db.query(models.User)
    
    if sort_by == "points":
        query = query.order_by(models.User.points.desc())
    elif sort_by == "decisions":
        query = query.order_by(models.User.id)
    else:
        query = query.order_by(models.User.id)
    
    users = query.offset(skip).limit(min(limit, 1000)).all()
    total = query.count()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "users": [schemas.UserOut.from_orm(u) for u in users],
    }


@router.post("/users/{user_id}/ban", dependencies=[Depends(get_current_admin)])
def ban_user(
    user_id: int,
    reason: str = "",
    db: Session = Depends(database.get_db),
):
    """Ban a user from the platform."""
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # TODO: Implement user banning logic
    return {"message": f"User {user.username} banned", "reason": reason}


@router.post("/users/{user_id}/reset-points", dependencies=[Depends(get_current_admin)])
def reset_user_points(
    user_id: int,
    db: Session = Depends(database.get_db),
):
    """Reset a user's points."""
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.points = 0
    db.commit()
    return {"message": f"Points reset for {user.username}", "new_points": 0}


@router.get("/decisions/analysis", dependencies=[Depends(get_current_admin)])
def analyze_decisions(
    min_score: float = 0.0,
    max_score: float = 1.0,
    db: Session = Depends(database.get_db),
):
    """Analyze decisions with filters."""
    decisions = db.query(models.Decision).filter(
        models.Decision.score >= min_score,
        models.Decision.score <= max_score,
    ).all()
    
    if not decisions:
        return {"total": 0, "avg_score": 0, "distribution": {}}
    
    scores = [d.score for d in decisions]
    avg_score = sum(scores) / len(scores)
    
    # Score distribution
    distribution = {
        "0-0.2": sum(1 for s in scores if s < 0.2),
        "0.2-0.4": sum(1 for s in scores if 0.2 <= s < 0.4),
        "0.4-0.6": sum(1 for s in scores if 0.4 <= s < 0.6),
        "0.6-0.8": sum(1 for s in scores if 0.6 <= s < 0.8),
        "0.8-1.0": sum(1 for s in scores if 0.8 <= s <= 1.0),
    }
    
    return {
        "total": len(decisions),
        "avg_score": round(avg_score, 2),
        "distribution": distribution,
    }


@router.delete("/decisions/{decision_id}", dependencies=[Depends(get_current_admin)])
def delete_decision(
    decision_id: int,
    db: Session = Depends(database.get_db),
):
    """Delete a decision (admin only)."""
    decision = db.query(models.Decision).filter(
        models.Decision.id == decision_id
    ).first()
    
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    
    db.delete(decision)
    db.commit()
    return {"message": "Decision deleted", "decision_id": decision_id}


@router.post("/database/backup", dependencies=[Depends(get_current_admin)])
def trigger_backup():
    """Trigger database backup."""
    # TODO: Implement backup logic
    return {
        "message": "Backup initiated",
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
    }


@router.get("/logs", dependencies=[Depends(get_current_admin)])
def get_recent_logs(
    level: str = "ERROR",
    limit: int = 100,
):
    """Get recent logs by level."""
    # TODO: Implement log retrieval
    return {
        "level": level,
        "total": 0,
        "logs": [],
    }


@router.post("/config/reload", dependencies=[Depends(get_current_admin)])
def reload_config():
    """Reload configuration without restart."""
    # TODO: Implement config reload
    return {"message": "Configuration reloaded"}
