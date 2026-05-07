## IPL Agentic AI Coaching Simulator

Real-time tactical cricket simulator where fans submit IPL captain-style decisions and receive **AI scoring powered by real cricket data**.

### ✨ What is implemented

- FastAPI backend with SQLite persistence
- Agentic decision pipeline (fan parser, historical evaluator, simulator, scorer)
- Decision submission endpoint with score + feedback + leaderboard update
- Runtime protections: user rate limiting + daily AI quota + in-memory decision cache
- **Optional Gemini integration with dynamic cricket statistics** ⭐ NEW
- Frontend dashboard integrated to backend APIs
- Auto-seeded default live match and historical decision records on startup

### 📊 NEW: Dynamic Cricket Data for AI Analysis

The system now feeds **real IPL statistics** to Gemini for contextual analysis:

**Data Sources:**
- **Bowler Stats** (`ipl_bowler_stats.json`): Economy rate, yorker accuracy, phase-specific performance (8 IPL bowlers)
- **Field Effectiveness** (`field_effectiveness.json`): Position-based catch probability and run prevention (14 field positions)
- **Matchup History** (`batsman_bowler_matchups.json`): Historical performance in specific batsman-bowler contests

**Example: Real Data Analysis**

User submits: `Pat Cummins bowling + Slip, Gully, Point field`

```
OLD: "Score based on general cricket principles"

NEW: "Pat Cummins economy: 8.2/over, yorker accuracy: 68%
      Slip field effectiveness vs pace: 85%, catch probability: 18%
      Gully effectiveness vs pace: 78%, Point: 72%
      ➜ Score: 0.78 (strong edge defense backed by real stats)"
```

### 🚀 Run locally

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Optional - Set up Gemini API (for real data analysis):
```bash
set GEMINI_API_KEY=your_key_here
set GEMINI_MODEL=gemini-2.0-flash
```

3. Start server:
```bash
uvicorn ipl_agentic_coach.backend.app.main:app --reload
```

4. Open dashboard:
```
http://127.0.0.1:8000/dashboard
```

### 🔄 Expand with Real Kaggle Data

To integrate real IPL datasets instead of sample data:

```bash
# Install Kaggle CLI
pip install kaggle pandas

# Download and process real IPL data
python ipl_agentic_coach/data/load_kaggle_data.py \
  --dataset vora1011/ipl-2023-cricket-analysis \
  --output ipl_agentic_coach/data

# For local CSV files:
python ipl_agentic_coach/data/load_kaggle_data.py \
  --csv path/to/ipl_matches.csv
```

See [DYNAMIC_DATA_GUIDE.md](docs/DYNAMIC_DATA_GUIDE.md) for detailed expansion instructions.

### 📡 Main APIs

- `POST /decisions/submit` → submit fan decision, get AI evaluation + leaderboard update
  - Response now includes `"data_insights"` (explains scoring using real statistics)
- `POST /decisions/evaluate` → evaluate decision without saving
- `GET /users/leaderboard/top` → top users by tactical points
- `GET /leaderboard/top` → top users (Cloud Run compatible)
- `GET /matches/current/live` → current match details
- `POST /ml/train` → train tactical prediction model using SQLite datasets
- `POST /ml/predict` → predict tactical score (0-1) from field, bowler, strategy, ball number
- `GET /ml/metrics` → view last training metrics

**Example response:**
```json
{
  "score": 0.78,
  "feedback": "Strong edge defense combining Slip (85% effectiveness), 
              Gully (78%), and Point (72%) against Pat Cummins' 68% yorker accuracy",
  "data_insights": "Analysis based on real IPL statistics showing Pat Cummins 
                   8.2 economy with Slip field creates strong fieldside pressure",
  "simulation_impact": {
    "wicket_chance": 0.35,
    "runs_saved": 4.2
  }
}
```

### ⚙️ Runtime controls

- Max user submissions: `20/hour` per username
- Daily AI evaluation quota: `950/day` 
- Decision evaluation cache TTL: `10 minutes`

### 🤖 ML Prediction Model

Train model locally from your datasets (`decisions` + `historical_decisions`):

```bash
python train_ml_model.py
```

Model artifacts are saved to:
- `ipl_agentic_coach/data/models/tactical_score_model.joblib`
- `ipl_agentic_coach/data/models/tactical_score_metrics.json`

Sample prediction request:

```bash
curl -X POST http://127.0.0.1:8000/ml/predict \
  -H "Content-Type: application/json" \
  -d "{\"field_input\":\"Slip, Gully, Point\",\"bowler_input\":\"Pat Cummins\",\"strategy_input\":\"Defend edges\",\"ball_number\":19}"
```

### ☁️ Google Cloud Deployment

#### Deploy backend to Cloud Run

```bash
gcloud run deploy ipl-coaching-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 3 \
  --set-env-vars GEMINI_API_KEY=your_key_here
```

#### Deploy frontend to Firebase Hosting

```bash
firebase deploy --only hosting
```

### 📚 Documentation

- [COPILOT.md](docs/COPILOT.md) - System architecture and design spec
- [DYNAMIC_DATA_GUIDE.md](docs/DYNAMIC_DATA_GUIDE.md) - Cricket data integration guide
- [ACCESSIBILITY_GUIDE.txt](docs/ACCESSIBILITY_GUIDE.txt) - Screen reader support details

### 🔧 Tech Stack

- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Frontend**: HTML5 + CSS3 + Vanilla JavaScript
- **AI**: Agentic Pipeline + Gemini API (optional)
- **Deployment**: Cloud Run + Firebase Hosting
- **Data**: Real IPL statistics (JSON-based, easily expandable)
