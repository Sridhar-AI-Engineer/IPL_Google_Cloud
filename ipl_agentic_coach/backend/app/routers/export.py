"""Export and bulk operations endpoints."""
import csv
import io
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from .. import crud, models, database, schemas
from ..pagination import PaginationParams, paginate, get_pagination_metadata

router = APIRouter(prefix="/export", tags=["Export"])


@router.get("/decisions/csv")
def export_decisions_csv(
    user_id: int = None,
    min_score: float = 0.0,
    max_score: float = 1.0,
    db: Session = Depends(database.get_db),
):
    """Export decisions to CSV format."""
    query = db.query(models.Decision).filter(
        models.Decision.score >= min_score,
        models.Decision.score <= max_score,
    )
    
    if user_id:
        query = query.filter(models.Decision.user_id == user_id)
    
    decisions = query.all()
    
    if not decisions:
        raise HTTPException(status_code=404, detail="No decisions found")
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        "ID", "User ID", "Match ID", "Ball Number", "Field Placement",
        "Bowling Change", "Strategy", "Score", "Feedback", "Timestamp"
    ])
    
    # Data
    for decision in decisions:
        writer.writerow([
            decision.id,
            decision.user_id,
            decision.match_id,
            decision.ball_number,
            decision.field_placement,
            decision.bowling_change,
            decision.tactical_strategy,
            decision.score,
            decision.feedback,
            decision.timestamp,
        ])
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=decisions.csv"}
    )


@router.get("/decisions/json")
def export_decisions_json(
    user_id: int = None,
    min_score: float = 0.0,
    max_score: float = 1.0,
    db: Session = Depends(database.get_db),
):
    """Export decisions to JSON format."""
    query = db.query(models.Decision).filter(
        models.Decision.score >= min_score,
        models.Decision.score <= max_score,
    )
    
    if user_id:
        query = query.filter(models.Decision.user_id == user_id)
    
    decisions = query.all()
    
    if not decisions:
        raise HTTPException(status_code=404, detail="No decisions found")
    
    data = []
    for decision in decisions:
        data.append({
            "id": decision.id,
            "user_id": decision.user_id,
            "match_id": decision.match_id,
            "ball_number": decision.ball_number,
            "field_placement": decision.field_placement,
            "bowling_change": decision.bowling_change,
            "tactical_strategy": decision.tactical_strategy,
            "score": decision.score,
            "feedback": decision.feedback,
            "timestamp": decision.timestamp,
        })
    
    return Response(
        content=json.dumps(data, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=decisions.json"}
    )


@router.get("/users/csv")
def export_users_csv(
    min_points: int = 0,
    db: Session = Depends(database.get_db),
):
    """Export users to CSV format."""
    users = db.query(models.User).filter(
        models.User.points >= min_points
    ).order_by(models.User.points.desc()).all()
    
    if not users:
        raise HTTPException(status_code=404, detail="No users found")
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow(["ID", "Username", "Email", "Points", "Decisions Count"])
    
    # Data
    for user in users:
        decisions_count = len(user.decisions)
        writer.writerow([
            user.id,
            user.username,
            user.email or "N/A",
            user.points,
            decisions_count,
        ])
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users.csv"}
    )


@router.get("/leaderboard/csv")
def export_leaderboard_csv(
    limit: int = 1000,
    db: Session = Depends(database.get_db),
):
    """Export leaderboard to CSV."""
    users = db.query(models.User).order_by(
        models.User.points.desc()
    ).limit(min(limit, 10000)).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["Rank", "Username", "Points", "Decisions"])
    
    for idx, user in enumerate(users, 1):
        writer.writerow([
            idx,
            user.username,
            user.points,
            len(user.decisions),
        ])
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leaderboard.csv"}
    )


@router.get("/analytics/json")
def export_analytics_json(
    db: Session = Depends(database.get_db),
):
    """Export analytics data to JSON."""
    from sqlalchemy import func
    
    total_users = db.query(func.count(models.User.id)).scalar() or 0
    total_decisions = db.query(func.count(models.Decision.id)).scalar() or 0
    avg_score = db.query(func.avg(models.Decision.score)).scalar() or 0
    
    top_users = db.query(
        models.User.username,
        models.User.points
    ).order_by(models.User.points.desc()).limit(10).all()
    
    data = {
        "exported_at": datetime.utcnow().isoformat(),
        "summary": {
            "total_users": total_users,
            "total_decisions": total_decisions,
            "average_score": round(float(avg_score), 2) if avg_score else 0,
        },
        "top_10_users": [
            {"username": u.username, "points": u.points}
            for u in top_users
        ],
    }
    
    return Response(
        content=json.dumps(data, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=analytics.json"}
    )


@router.post("/decisions/batch-import")
async def batch_import_decisions(
    file: bytes,
    format: str = "json",
    user_id: int = None,
    db: Session = Depends(database.get_db),
):
    """Import multiple decisions from file (JSON)."""
    try:
        decisions_data = json.loads(file)
        
        if not isinstance(decisions_data, list):
            raise HTTPException(
                status_code=400,
                detail="JSON must be an array of decisions"
            )
        
        imported_count = 0
        
        for item in decisions_data[:1000]:  # Limit to 1000 per import
            try:
                decision = schemas.DecisionCreate(
                    user_id=user_id or item.get("user_id"),
                    match_id=item.get("match_id", 1),
                    ball_number=item.get("ball_number", 1),
                    field_placement=item.get("field_placement", "off"),
                    bowling_change=item.get("bowling_change", "none"),
                    tactical_strategy=item.get("tactical_strategy", ""),
                )
                
                # TODO: Create decision via crud
                imported_count += 1
            except Exception as e:
                continue  # Skip invalid rows
        
        return {"imported": imported_count, "total": len(decisions_data)}
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
