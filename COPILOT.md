# IPL Coaching Simulator – Google Cloud Optimized Spec (For GitHub Copilot)

## 1. Product Vision

Build an **IPL Coaching Simulator** where fans act as captains during live IPL matches.  
Core idea:

- Fans make tactical decisions:
  - Field placement
  - Bowler selection
  - Strategy description
- AI evaluates decisions in real-time
- Leaderboard ranks fans globally
- Entire system **heavily leverages free Google services** to impress Google hackathon judges and stay within **$0–$5/month**.

Target:  
- Maximize **Google ecosystem usage** (Firebase, Cloud Run, Gemini, BigQuery, etc.).  
- Stay within **free tier limits** so it effectively costs **$0 per month**.

***

## 2. High-Level Architecture (Google-First, Free-Tier)

### 2.1 Frontend

- **Firebase Hosting** (primary static hosting)
  - Hosts SPA (React/Vue/Vanilla) with:
    - Tactical dashboard UI
    - Live field animation
    - Leaderboard
  - Uses:
    - **Google Fonts**
    - **Google Material Icons**
    - **Google Charts**
    - **TensorFlow.js** for local predictions

- **Core UX Features**
  - Hero + navigation: Watch Live, Decisions, Live Field, Leaderboard
  - Decision Form: field placement, bowler, strategy text, submit button
  - Live Preview: shows combined tactical summary
  - Live Field Animation: visual depiction of ball + fielders
  - Leaderboard: global ranking, tiers, badges
  - Analytics/Insights: charts and data visualizations

### 2.2 Backend

- **Cloud Run** (backend API)
  - Hosts a Python or Node.js service (e.g. `app:app` in Flask/FastAPI or Express).
  - Responsibilities:
    - Handle `/decisions/submit`
    - Call **Gemini API (AI Studio)** for tactical analysis
    - Persist decisions and scores to **Firestore**
    - Update summary aggregates for leaderboard
  - Deployed in `us-central1`
  - Config:
    - `min-instances = 0` (scales to zero, no idle cost)
    - `max-instances = 3–5`
    - Concurrency ≈ 80
    - CPU throttling enabled

- **Firebase Cloud Functions** (optional background jobs)
  - Recalculate leaderboard periodically
  - Perform heavy off-line aggregation tasks if needed

### 2.3 Data Layer

- **Cloud Firestore** (Native)
  - Collections:
    - `users` – profile, total_score, rank, country
    - `decisions` – per decision, score, bowler, positions, strategy, timestamp
    - `matches` – match meta (teams, scores, overs, context)
  - Used for:
    - Leaderboard
    - User stats
    - Historical tactical decisions

- **Firebase Realtime Database**
  - Used for **live, high-frequency data**:
    - Live match score
    - Live active users count
    - Live leaderboard snapshot (top N)
  - Frontend subscribes via Firebase SDK and updates UI instantly.

- **Cloud Storage**
  - Stores static assets:
    - Logos, images, stadium backgrounds
    - Possibly TF.js model files
  - May host exported ML models (`model.json` + weights).

- **BigQuery**
  - Periodically (batch) ingest summarized decision data (from Firestore).
  - Used to generate:
    - Field position effectiveness
    - Bowler effectiveness per phase
    - User behavior analytics (what works in death overs, etc.)

***

## 3. Google Services to Use (and How)

### 3.1 Identity & Engagement

1. **Firebase Authentication**
   - Sign-in with Google (primary).
   - Optionally email/password.
   - Used for:
     - Identifying users in decisions
     - Personalized leaderboard position (“Your rank” card)
   - Frontend: Firebase JS SDK.

2. **Firebase Cloud Messaging (FCM)**
   - Web push notifications:
     - “Over 19 starting – submit your field!”
     - “You moved up to rank #23”
   - Helps show engagement capability.

3. **Firebase Analytics**
   - Track events:
     - `tactical_decision_submitted`
     - `leaderboard_viewed`
     - `field_position_selected`
     - `bowler_selected`
   - Used to show metrics in hackathon pitch.

4. **Firebase Performance Monitoring**
   - Monitor:
     - API response times (AI scoring latency)
     - Page loads
   - Use to prove:
     - “95% of decisions evaluated < 1 second”.

### 3.2 AI & ML

1. **Gemini API (AI Studio, not Vertex AI)**
   - Use `google-generativeai` client library.
   - Use **Flash / cheap models**:
     - e.g. `gemini-2.0-flash-exp`.
   - Use cases:
     - Single combined call per decision:
       - Score (0–100)
       - Wicket chance
       - Runs saved
       - Historical fit
       - Text feedback
   - Apply:
     - Request caching
     - Rate limiting
     - Combined prompts (multi-agent reasoning but one API call).

2. **TensorFlow.js**
   - Optional: simple local ML model in browser.
   - Use for fast, offline-ish estimates:
     - Quick wicket probability / runs saved baseline.
   - Flow:
     - Pretrain model (in Colab with Cloud GPU).
     - Export to TF.js.
     - Load from Cloud Storage in frontend.
   - Strategy:
     - Use TF.js for instant estimation.
     - Use Gemini for richer explanation and final score.

3. **Google Colab**
   - Training playground for modeling using historical data.
   - Save trained models to Cloud Storage.

### 3.3 Data & Analytics

1. **Firestore (Native Mode)**
   - Primary OLTP store.
   - High-level schema:

     - `users/{userId}`
       - `displayName`
       - `photoURL`
       - `total_score`
       - `rank`
       - `country`
       - `created_at`

     - `decisions/{decisionId}`
       - `user_id`
       - `match_id`
       - `positions`: array
       - `bowler`
       - `strategy`
       - `ai_score`
       - `wicket_chance`
       - `runs_saved`
       - `created_at`

     - `matches/{matchId}`
       - `teams`
       - `current_over`
       - `target`
       - `context`
       - `status`

2. **Firebase Realtime Database**
   - Example keys:
     - `/live-match/score`
     - `/live-match/over`
     - `/live-match/activeUsers`
     - `/leaderboard/top10`
   - Cloud Run/Functions update these on changes.
   - Clients subscribe via `onValue()`.

3. **BigQuery**
   - Table examples:
     - `ipl_simulator.decisions_flat`
     - `ipl_simulator.user_metrics`
   - Run scheduled ETL/export from Firestore to BigQuery.
   - Use for advanced queries:
     - Most effective field positions in death overs.
     - Bowler vs match phase vs tactical scores.

4. **Looker Studio (Data Studio)**
   - Connect to BigQuery.
   - Create dashboards:
     - Total users
     - Total decisions
     - Avg score per over
     - Engagement metrics
   - Optionally embed screenshot or read-only link in app or pitch deck.

### 3.4 Visualization & UI Libraries

1. **Google Charts**
   - Line charts:
     - User score over overs.
   - Bar charts:
     - Bowler performance comparison.
   - Pie charts or radar:
     - Field position usage.
   - Heatmap-like: simulate via custom chart + styling.

2. **Google Fonts**
   - Use a Material-friendly font:
     - e.g. `Inter`, `Roboto`, or `Google Sans` alternative.

3. **Google Material Icons**
   - Use icons for:
     - Navigation: `sports_cricket`, `tv`, `leaderboard`, `bolt`
     - Status: `check_circle`, `warning`, `info`, `error`

### 3.5 Extra Google Integrations (Optional but Cool)

1. **Google Maps**
   - Show global fan map:
     - Marker per active user’s approximate region/country.
   - Data: from user profile (`country` / `city`) or rough IP-based geo.

2. **YouTube Data API**
   - Create “Tactical Learning” section:
     - Embed top IPL tactic analysis videos.
   - Search term examples:
     - “IPL death overs field setting”
     - “cricket tactics analysis”

3. **Google reCAPTCHA v3**
   - Protect decision submission and leaderboard from bots.

4. **Google Translate API**
   - Optional localization:
     - Hindi, Telugu, Tamil, etc.
   - At minimum, support static translations of main CTAs.

***

## 4. Backend Behavior (Cloud Run Service)

### 4.1 Endpoints

- `POST /decisions/submit`
  - Input:
    - `user_id`
    - `match_id`
    - `field_positions` (array of position IDs)
    - `bowler` (name + type)
    - `strategy` (string)
  - Behavior:
    1. Validate user auth (Firebase token).
    2. Enforce **user rate limiting** (e.g. 20 decisions/hour).
    3. Enforce **daily AI quota** (~950 calls/day; keep under 1000 free).
    4. Compute **field hash** for caching.
    5. Check local in-memory or Redis-style cache (if same pattern seen).
    6. If not cached:
       - Call Gemini API with combined prompt.
       - Parse JSON-like output:
         - `score`, `wicket_chance`, `runs_saved`, `historical_fit`, `feedback`.
       - Store AI response in cache.
    7. Save decision to Firestore.
    8. Update user’s cumulative score in Firestore.
    9. Optionally trigger Cloud Function to refresh leaderboard snapshot in Realtime DB.
    10. Return AI analysis payload.

- `GET /leaderboard/top`
  - Reads from Realtime DB `/leaderboard/top10` for near-zero latency and cost.

- `GET /health`
  - Simple “OK” for Cloud Run health check.

### 4.2 Gemini Prompt Shape (Single Call)

- Prompt template includes:
  - Match context (target, overs, score).
  - Field positions (semantic description).
  - Bowler type.
  - Strategy text.
- Response is **strict JSON**.

***

## 5. Free Tier & Cost Constraints

Goal: run entirely in **Google free tiers**, leaving $5 as safety buffer.

Key free tier limits (approx, to respect in code):

- Cloud Run:
  - 2M requests/month free (us-central1).
- Gemini API (AI Studio):
  - ~1,000–1,500 requests/day free (Flash models).
- Firestore:
  - 50K reads/day, 20K writes/day, 1GB storage.
- Storage:
  - 5GB standard storage.
- Firebase Hosting:
  - 10GB storage, ~360MB/day data transfer.
- Realtime Database:
  - 1GB storage, 10GB/month download.
- Cloud Functions:
  - 2M invocations/month.
- BigQuery:
  - 1TB query data/month.

Implementation requirements:

- **Rate-limit** Gemini calls per day.
- **Cache** repeated decisions (field + bowler + rough strategy).
- Avoid noisy Firestore writes (batch where appropriate).
- Use Firebase Hosting and Cloud Storage for static content to offload Cloud Run.
- Use Realtime DB for high-frequency live updates, not Firestore.

***

## 6. Frontend Requirements for Copilot

### 6.1 UI/UX Standards

- **Material Design 3** inspired:
  - Elevated cards (large radius 16–20px).
  - Tonal surfaces for dark mode (Google Cloud dark theme).
  - Strong contrast, proper typography scale.

- **Core Screens:**
  1. **Landing / Hero**
     - “Turn IPL fans into tactical captains”
     - Buttons:
       - Watch Live
       - Start Tactical Session
       - View Growth Signals
     - Badges:
       - “Powered by Google Cloud”
       - “Gemini AI Tactical Engine”

  2. **Decision Center**
     - Field diagram with 14 clickable positions.
     - Bowler dropdown.
     - Strategy input.
     - Submit button with loading, success, error states.
     - Live AI Preview component.

  3. **Live Field View**
     - Animated cricket field.
     - Ball + fielder animations.
     - Overlay predicted trajectory + fielder highlight after decision.

  4. **Leaderboard**
     - Top 10 global ranks (with tiers: Master Tactician, Strategic Coach, etc.).
     - Sticky “Your Rank” widget.

  5. **Analytics / Growth Signals**
     - Google Charts-driven visualizations:
       - Engagement metrics.
       - Field effectiveness.
       - Bowler performance.

### 6.2 Authentication Flow

- On load:
  - Show “Sign in with Google” button (Firebase Auth).
  - Once logged in:
    - Show avatar + display name.
    - Allow decisions linked to user.

### 6.3 Real-Time Features

- Subscribe to Realtime DB:
  - `/live-match/score` → Update score widgets.
  - `/leaderboard/top10` → Live leaderboard updates.

***

## 7. Deployment Steps (For Automation / Scripts)

1. **Firebase Setup**
   - `firebase init` (select: Hosting, Firestore, Functions, Realtime Database, Analytics).
   - Deploy frontend:
     - `firebase deploy --only hosting`.

2. **Cloud Run API**
   - Build & deploy:
     - `gcloud run deploy ipl-coaching-api --source . --region=us-central1 --allow-unauthenticated --min-instances=0 --max-instances=3 --set-env-vars=GEMINI_API_KEY=...`

3. **Firestore & Realtime DB**
   - Enable in Firebase console.
   - Define initial security rules for authenticated access.

4. **BigQuery**
   - Create dataset `ipl_simulator`.
   - Set up ETL/exports from Firestore or Cloud Functions.

5. **Budget & Alerts**
   - Create budget in Cloud Billing with alerts at 20%, 50%, 90% of $5.

***

## 8. What Copilot Should Help With

Copilot can assist with:

- Generating:
  - React/Next/Vue components for dashboard.
  - Firebase integration boilerplate.
  - Cloud Run service handlers in Python/Node.
  - Gemini prompt and parsing logic.
  - Firestore/Realtime DB code (CRUD operations).
  - BigQuery queries.
  - Charts configuration using Google Charts.

- Ensuring:
  - Free-tier aware code (rate limiting, caching).
  - Proper Google SDK usage.
  - Clean separation of frontend (Firebase Hosting) and backend (Cloud Run).
