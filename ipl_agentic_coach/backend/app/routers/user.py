from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas, database

router = APIRouter()

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = crud.get_user_by_username(db, user.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    return crud.create_user(db, user)


@router.post("/create", response_model=schemas.UserOut)
def create_user_explicit(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Create a new user. Returns user details with ID and initial points."""
    existing = crud.get_user_by_username(db, user.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    return crud.create_user(db, user)


@router.post("/ensure", response_model=schemas.UserOut)
def ensure_user(user: schemas.UserEnsure, db: Session = Depends(get_db)):
    return crud.ensure_user(db, user)


@router.get("/", response_model=list[schemas.UserOut])
def list_users(db: Session = Depends(get_db)):
    return crud.get_all_users(db)


@router.get("/{user_id}", response_model=schemas.UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/leaderboard/top", response_model=list[schemas.LeaderboardEntry])
def get_leaderboard(limit: int = 10, db: Session = Depends(get_db)):
    safe_limit = min(max(limit, 1), 50)
    return crud.get_leaderboard(db, limit=safe_limit)