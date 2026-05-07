
# **COMPLETE PLAN: Agentic AI IPL Coaching Simulator**

---

## **PHASE 1: Project Planning & Architecture**

### **1. Objective**

* Fans act as virtual cricket captains during IPL matches.
* They make **real-time decisions**: field placements, bowling changes.
* AI scores these decisions based on:

  * Historical data
  * Captain’s actual decisions
  * Lightweight simulation
* Provides **AI-driven feedback** and maintains a **leaderboard**.

---

### **2. Key Features**

1. **User Management**

   * Register, login
   * Track points/score
2. **Match Dashboard**

   * Live IPL ball tracker (mock/live data)
   * Fan decision input panel
3. **Agentic AI Pipeline**

   * FanDecisionAgent → convert inputs into structured moves
   * HistoricalEvaluatorAgent → compare with historical scenarios
   * SimulatorAgent → predict impact of move
   * ScoringAgent → calculate score and feedback
4. **Leaderboard**

   * Shows top tactical fans
   * Updates dynamically
5. **AI Feedback**

   * Natural language feedback: “Good choice! Spinner might be risky next ball.”

---

### **3. Tech Stack**

| Layer         | Technology                                                                                               |
| ------------- | -------------------------------------------------------------------------------------------------------- |
| Backend       | FastAPI                                                                                                  |
| Database      | SQLite                                                                                                   |
| Frontend      | HTML5 + CSS5 + JS (vanilla, optionally HTMX/Alpine.js for interactivity)                                 |
| AI / Agents   | LangChain (agent orchestration), LangGraph (workflow visualization), optionally OpenAI API for reasoning |
| Deployment    | Local-first, optional GCP Cloud Run for live demo under $5                                               |
| Analytics     | Pandas + NumPy                                                                                           |
| Visualization | Plotly / Matplotlib (leaderboards & feedback charts)                                                     |

---

## **PHASE 2: Project Structure**

```text
ipl_agentic_coach/
│
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI entrypoint
│   │   ├── models.py             # SQLAlchemy models
│   │   ├── database.py           # SQLite connection
│   │   ├── schemas.py            # Pydantic models
│   │   ├── crud.py               # DB operations
│   │   └── routers/
│   │       ├── user.py           # Users / leaderboard
│   │       ├── match.py          # Match updates / ball tracking
│   │       └── decision.py       # Fan decisions + scoring
│   │
│   └── requirements.txt
│
├── ai_agents/
│   ├── fan_decision_agent.py
│   ├── historical_evaluator_agent.py
│   ├── simulator_agent.py
│   ├── scoring_agent.py
│   └── agentic_pipeline.py       # Combines all agents
│
├── frontend/
│   ├── index.html
│   ├── dashboard.html
│   ├── css/styles.css
│   └── js/dashboard.js
│
├── data/
│   ├── historical_matches.db     # SQLite with historical IPL data
│   └── live_data.json            # Mock/live IPL feed
│
├── utils/
│   ├── analytics.py
│   └── visualizations.py
│
└── README.md
```

---

## **PHASE 3: Database Design**

### **SQLite Tables**

1. **Users**

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    email TEXT,
    points INTEGER DEFAULT 0
);
```

2. **Matches**

```sql
CREATE TABLE matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_a TEXT,
    team_b TEXT,
    date TEXT,
    status TEXT
);
```

3. **Decisions**

```sql
CREATE TABLE decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    match_id INTEGER,
    ball_number INTEGER,
    field_placement TEXT,
    bowling_change TEXT,
    timestamp TEXT,
    score REAL,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(match_id) REFERENCES matches(id)
);
```

4. **Historical Decisions**

```sql
CREATE TABLE historical_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER,
    ball_number INTEGER,
    captain_move TEXT,
    situation TEXT,
    expected_score REAL
);
```

---

## **PHASE 4: Agentic AI Pipeline**

### **1. FanDecisionAgent**

* Converts raw fan input → structured tactical moves
* Example: `"Move mid-off closer, bring spinner"` → `{field: "mid-off closer", bowler: "spinner"}`

### **2. HistoricalEvaluatorAgent**

* Checks historical IPL scenarios
* Scores similarity to captain moves or ideal scenarios

### **3. SimulatorAgent**

* Lightweight predictive simulation (next 1–3 balls)
* Estimates runs/wickets saved or conceded

### **4. ScoringAgent**

* Combines:

  * Captain comparison (0–1)
  * Historical merit (0–1)
  * Simulation impact (0–1)
* Returns **total score + AI feedback**

---

## **PHASE 5: Frontend Dynamic Dashboard**

* **Live IPL feed** (mock or minimal API)
* **Decision panel**

  * Dropdowns for field placement, bowler change
  * Submit button → triggers agentic AI pipeline
* **Leaderboard**

  * Real-time update
* **Feedback Panel**

  * Shows AI reasoning in natural language
* **Visualization**

  * Graphs of points, predicted outcomes

---

## **PHASE 6: Local Development Steps**

1. **Install dependencies**

```bash
pip install fastapi uvicorn sqlalchemy pydantic pandas matplotlib plotly langchain
```

2. **Run backend**

```bash
uvicorn backend.app.main:app --reload
```

3. **Open dashboard**

```text
http://127.0.0.1:8000/dashboard.html
```

4. **Test agentic pipeline**

* Submit fan decisions
* See scoring, leaderboard, AI feedback

---

## **PHASE 7: Optional GCP Deployment (Under $5)**

1. **Use Cloud Run / e2-micro instance**
2. **Deploy FastAPI app + SQLite**
3. **Keep instance minimal**: only demo use → cost < $5
4. **Use Cloud Storage for static frontend files** (optional)
5. **Result**: live URL for demo → impress interviewers

---

## **PHASE 8: Competition & Interview Winning Strategies**

* Highlight **Agentic AI orchestration**:

  * Each agent has clear responsibilities
  * LangChain orchestrates reasoning
  * LangGraph shows workflow visualization
* Showcase **dynamic leaderboard + real-time feedback**
* Show **predictive simulation + tactical merit scoring**
* Optional **extensions**:

  * Pitch/weather agent
  * Opponent modeling agent
  * Fan coaching agent → AI provides tactical suggestions

---

✅ **Deliverables for Showcase**

1. Fully functional **FastAPI backend + SQLite**
2. **Agentic AI pipeline** with 4 agents
3. **Frontend dashboard** with live leaderboard + AI feedback
4. **Optional live GCP deployment** for demo link
5. **LangGraph workflow visualization**
6. **Documentation / README** explaining agents, scoring, and architecture

