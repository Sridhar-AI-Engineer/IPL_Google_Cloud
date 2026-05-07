import os

# Base project folder
project_name = "ipl_agentic_coach"

# Folder structure
folders = {
    "backend": [
        "app",
        "app/routers",
    ],
    "ai_agents": [],
    "frontend": [
        "frontend/css",
        "frontend/js"
    ],
    "data": [],
    "utils": []
}

# Files with starter code
files = {
    # Backend
    "backend/app/main.py": """from fastapi import FastAPI
from app.routers import user, match, decision

app = FastAPI(title="IPL Agentic AI Coaching Simulator")

app.include_router(user.router, prefix="/users", tags=["users"])
app.include_router(match.router, prefix="/matches", tags=["matches"])
app.include_router(decision.router, prefix="/decisions", tags=["decisions"])

@app.get("/")
def root():
    return {"message": "Welcome to the IPL Agentic AI Coaching Simulator!"}
""",

    "backend/app/models.py": """from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String)
    points = Column(Integer, default=0)

class Match(Base):
    __tablename__ = 'matches'
    id = Column(Integer, primary_key=True)
    team_a = Column(String)
    team_b = Column(String)
    date = Column(String)
    status = Column(String)

class Decision(Base):
    __tablename__ = 'decisions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    match_id = Column(Integer, ForeignKey('matches.id'))
    ball_number = Column(Integer)
    field_placement = Column(String)
    bowling_change = Column(String)
    timestamp = Column(String)
    score = Column(Float)
""",

    "backend/app/database.py": """from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base

DATABASE_URL = "sqlite:///./data/historical_matches.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
""",

    "backend/app/schemas.py": """from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    points: Optional[int] = 0

    class Config:
        orm_mode = True
""",

    "backend/app/crud.py": """from sqlalchemy.orm import Session
from app import models, schemas

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(username=user.username, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
""",

    "backend/app/routers/user.py": """from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import crud, schemas

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db, user)
""",

    "backend/app/routers/match.py": """from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_matches():
    return {"matches": "List of matches will be here"}
""",

    "backend/app/routers/decision.py": """from fastapi import APIRouter

router = APIRouter()

@router.post("/")
def submit_decision():
    return {"message": "Decision received"}
""",

    "backend/app/requirements.txt": "fastapi\nuvicorn\nsqlalchemy\npydantic\npandas\nmatplotlib\nplotly\nlangchain\n",

    # AI Agents
    "ai_agents/fan_decision_agent.py": """class FanDecisionAgent:
    def parse_decision(self, input_str):
        # Convert fan input into structured move
        return {"field": "mid-off", "bowler": "spinner"}
""",

    "ai_agents/historical_evaluator_agent.py": """class HistoricalEvaluatorAgent:
    def evaluate(self, move, match_context):
        # Compare move to historical data
        return 0.8  # Tactical merit score
""",

    "ai_agents/simulator_agent.py": """class SimulatorAgent:
    def simulate(self, move, match_context):
        # Predict outcome of next balls
        return {"predicted_runs": 4, "predicted_wickets": 0}
""",

    "ai_agents/scoring_agent.py": """class ScoringAgent:
    def score(self, tactical_score, simulation_score):
        # Combine scores to final score
        return tactical_score * 0.6 + simulation_score * 0.4
""",

    "ai_agents/agentic_pipeline.py": """from ai_agents.fan_decision_agent import FanDecisionAgent
from ai_agents.historical_evaluator_agent import HistoricalEvaluatorAgent
from ai_agents.simulator_agent import SimulatorAgent
from ai_agents.scoring_agent import ScoringAgent

class AgenticPipeline:
    def __init__(self):
        self.fan_agent = FanDecisionAgent()
        self.historical_agent = HistoricalEvaluatorAgent()
        self.simulator_agent = SimulatorAgent()
        self.scoring_agent = ScoringAgent()

    def process_decision(self, input_str, match_context):
        move = self.fan_agent.parse_decision(input_str)
        tactical_score = self.historical_agent.evaluate(move, match_context)
        simulation_result = self.simulator_agent.simulate(move, match_context)
        simulation_score = 1 - simulation_result["predicted_runs"]/10  # Example scoring
        final_score = self.scoring_agent.score(tactical_score, simulation_score)
        return {"final_score": final_score, "simulation": simulation_result}
""",

    # Frontend
    "frontend/index.html": """<!DOCTYPE html>
<html>
<head>
    <title>IPL Coaching Simulator</title>
</head>
<body>
<h1>Welcome to IPL Agentic AI Coaching Simulator</h1>
<a href="dashboard.html">Go to Dashboard</a>
</body>
</html>
""",

    "frontend/dashboard.html": """<!DOCTYPE html>
<html>
<head>
    <title>Dashboard</title>
    <link rel="stylesheet" href="css/styles.css">
</head>
<body>
<h2>Live Match Dashboard</h2>
<div id="leaderboard"></div>
<div id="decision-panel">
    <input type="text" id="decision-input" placeholder="Enter your decision">
    <button onclick="submitDecision()">Submit</button>
</div>
<div id="ai-feedback"></div>
<script src="js/dashboard.js"></script>
</body>
</html>
""",

    "frontend/css/styles.css": """body { font-family: Arial; margin: 20px; }""",
    "frontend/js/dashboard.js": """function submitDecision() {
    const input = document.getElementById('decision-input').value;
    console.log('Decision submitted:', input);
    alert('Decision submitted! AI scoring coming soon.');
}""",

    # Data
    "data/historical_matches.db": "",
    "data/live_data.json": "{}\n",

    # Utils
    "utils/analytics.py": "# Analytics helper functions\n",
    "utils/visualizations.py": "# Visualization helper functions\n",

    # README
    "README.md": "# IPL Agentic AI Coaching Simulator\nProject scaffold with AI agents and FastAPI backend."
}

# Create folders
for root, subfolders in folders.items():
    for folder in subfolders:
        path = os.path.join(project_name, folder)
        os.makedirs(path, exist_ok=True)
        print(f"Created folder: {path}")

# Create files with content
for file_path, content in files.items():
    full_path = os.path.join(project_name, file_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)  # Ensure folder exists
    with open(full_path, "w") as f:
        f.write(content)
    print(f"Created file: {full_path}")

print("\nFull project skeleton with starter code created successfully!")