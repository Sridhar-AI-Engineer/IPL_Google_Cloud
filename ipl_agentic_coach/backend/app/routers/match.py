from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas, database

router = APIRouter()

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.MatchOut)
def create_match(match: schemas.MatchCreate, db: Session = Depends(get_db)):
    return crud.create_match(db, match)


@router.get("/", response_model=list[schemas.MatchOut])
def list_matches(db: Session = Depends(get_db)):
    return crud.get_matches(db)


@router.get("/{match_id}", response_model=schemas.MatchOut)
def get_match(match_id: int, db: Session = Depends(get_db)):
    match = crud.get_match(db, match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match


@router.get("/current/live", response_model=schemas.MatchOut)
def get_current_match(db: Session = Depends(get_db)):
    match = crud.ensure_default_match(db)
    return match