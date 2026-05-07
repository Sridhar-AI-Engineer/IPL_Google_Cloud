"""
Analytics Router
================
Exposes IPL analytics charts via FastAPI endpoints.
Charts are generated using Plotly (interactive JSON) and Matplotlib (static PNG).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse

# Ensure package is importable from backend/app/routers/
_root = Path(__file__).resolve().parents[4]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from ipl_agentic_coach.utils.analytics import (
    all_charts_json,
    fig_to_json,
    get_bowler_economy_chart,
    get_field_effectiveness_heatmap,
    get_leaderboard_chart,
    get_score_distribution,
    get_score_timeline,
    get_strategy_breakdown,
    PLOTLY_AVAILABLE,
)
from ipl_agentic_coach.utils.visualizations import (
    is_available as matplotlib_available,
    plot_bowler_economy,
    plot_dashboard_overview,
    plot_leaderboard_bar,
    plot_score_history,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ── Plotly JSON Endpoints ──────────────────────────────────────────────────────

@router.get("/leaderboard-chart")
def leaderboard_chart(top_n: int = Query(10, ge=1, le=50)):
    """Interactive Plotly leaderboard bar chart (JSON)."""
    fig = get_leaderboard_chart(top_n=top_n)
    data = fig_to_json(fig)
    if data is None:
        raise HTTPException(503, "Plotly not available. Install: pip install plotly")
    return JSONResponse(content={"chart": data, "type": "bar", "library": "plotly"})


@router.get("/score-distribution")
def score_distribution():
    """Interactive Plotly histogram of fan decision scores (JSON)."""
    fig = get_score_distribution()
    data = fig_to_json(fig)
    if data is None:
        raise HTTPException(503, "Plotly not available.")
    return JSONResponse(content={"chart": data, "type": "histogram", "library": "plotly"})


@router.get("/score-timeline")
def score_timeline():
    """Interactive Plotly line chart of avg score per ball (JSON)."""
    fig = get_score_timeline()
    data = fig_to_json(fig)
    if data is None:
        raise HTTPException(503, "Plotly not available.")
    return JSONResponse(content={"chart": data, "type": "line", "library": "plotly"})


@router.get("/bowler-chart")
def bowler_chart():
    """Bowler economy comparison chart (JSON)."""
    fig = get_bowler_economy_chart()
    data = fig_to_json(fig)
    if data is None:
        raise HTTPException(503, "Plotly not available.")
    return JSONResponse(content={"chart": data, "type": "bar", "library": "plotly"})


@router.get("/field-heatmap")
def field_heatmap():
    """Field placement effectiveness heatmap (JSON)."""
    fig = get_field_effectiveness_heatmap()
    data = fig_to_json(fig)
    if data is None:
        raise HTTPException(503, "Plotly not available.")
    return JSONResponse(content={"chart": data, "type": "heatmap", "library": "plotly"})


@router.get("/strategy-breakdown")
def strategy_breakdown():
    """Fan strategy breakdown pie/donut chart (JSON)."""
    fig = get_strategy_breakdown()
    data = fig_to_json(fig)
    if data is None:
        raise HTTPException(503, "Plotly not available.")
    return JSONResponse(content={"chart": data, "type": "pie", "library": "plotly"})


@router.get("/all-charts")
def all_charts():
    """All Plotly charts combined as a single JSON response."""
    return JSONResponse(content={
        "charts": all_charts_json(),
        "library": "plotly",
        "plotly_available": PLOTLY_AVAILABLE,
    })


# ── Matplotlib PNG Endpoints ───────────────────────────────────────────────────

@router.get("/static/leaderboard")
def static_leaderboard():
    """Matplotlib leaderboard PNG (base64 data URI)."""
    if not matplotlib_available():
        raise HTTPException(503, "Matplotlib not available. Install: pip install matplotlib")
    return JSONResponse(content={"image": plot_leaderboard_bar(), "library": "matplotlib"})


@router.get("/static/score-history")
def static_score_history():
    """Matplotlib score history PNG (base64 data URI)."""
    if not matplotlib_available():
        raise HTTPException(503, "Matplotlib not available.")
    return JSONResponse(content={"image": plot_score_history(), "library": "matplotlib"})


@router.get("/static/bowler-economy")
def static_bowler_economy():
    """Matplotlib bowler economy PNG (base64 data URI)."""
    if not matplotlib_available():
        raise HTTPException(503, "Matplotlib not available.")
    return JSONResponse(content={"image": plot_bowler_economy(), "library": "matplotlib"})


@router.get("/static/dashboard")
def static_dashboard():
    """Full multi-panel Matplotlib dashboard PNG (base64 data URI)."""
    if not matplotlib_available():
        raise HTTPException(503, "Matplotlib not available.")
    return JSONResponse(content={"image": plot_dashboard_overview(), "library": "matplotlib"})


# ── HTML Dashboard ─────────────────────────────────────────────────────────────

@router.get("/dashboard", response_class=HTMLResponse)
def analytics_dashboard():
    """
    Interactive HTML analytics dashboard embedding all Plotly charts.
    Served directly — no additional HTML file required.
    """
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>IPL Fan Coach — Analytics Dashboard</title>
  <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
  <style>
    :root {
      --bg: #0A0E1A; --panel: #12182B; --orange: #FF6B35;
      --gold: #FFD700; --blue: #1E3A5F; --white: #FFFFFF;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: var(--bg); color: var(--white); font-family: 'Segoe UI', sans-serif; }
    header {
      background: var(--panel); border-bottom: 2px solid var(--orange);
      padding: 1rem 2rem; display: flex; align-items: center; gap: 1rem;
    }
    header h1 { font-size: 1.5rem; color: var(--gold); }
    .badge {
      background: var(--blue); border: 1px solid var(--orange);
      border-radius: 12px; padding: 0.2rem 0.65rem; font-size: 0.75rem; color: var(--white);
    }
    .grid {
      display: grid; grid-template-columns: repeat(auto-fit, minmax(520px, 1fr));
      gap: 1.25rem; padding: 1.5rem;
    }
    .chart-card {
      background: var(--panel); border: 1px solid var(--blue);
      border-radius: 10px; padding: 1rem;
      box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }
    .chart-title {
      font-size: 0.9rem; color: var(--gold); margin-bottom: 0.5rem;
      border-bottom: 1px solid var(--blue); padding-bottom: 0.4rem;
    }
    .chart-box { width: 100%; height: 340px; }
    .refreshBtn {
      background: var(--orange); color: white; border: none;
      border-radius: 6px; padding: 0.5rem 1.25rem; cursor: pointer;
      font-size: 0.85rem; font-weight: 600; margin-left: auto;
    }
    .refreshBtn:hover { background: #e05520; }
    .status { font-size: 0.75rem; color: #aaa; }
    #errorBanner {
      display: none; background: #c0392b; color: white;
      padding: 0.75rem 2rem; font-size: 0.9rem;
    }
  </style>
</head>
<body>
<header>
  <span style="font-size:1.8rem">🏏</span>
  <h1>IPL Fan Coach — Analytics Dashboard</h1>
  <span class="badge">Plotly</span>
  <span class="badge">Python</span>
  <button class="refreshBtn" onclick="loadAll()">🔄 Refresh</button>
</header>
<div id="errorBanner"></div>
<div class="grid">
  <div class="chart-card">
    <div class="chart-title">🏆 Fan Leaderboard</div>
    <div class="chart-box" id="chart-leaderboard"></div>
  </div>
  <div class="chart-card">
    <div class="chart-title">📊 Score Distribution</div>
    <div class="chart-box" id="chart-scores"></div>
  </div>
  <div class="chart-card">
    <div class="chart-title">⚡ Score Timeline</div>
    <div class="chart-box" id="chart-timeline"></div>
  </div>
  <div class="chart-card">
    <div class="chart-title">🎯 Bowler Economy</div>
    <div class="chart-box" id="chart-bowler"></div>
  </div>
  <div class="chart-card">
    <div class="chart-title">🗺️ Field Placement Heatmap</div>
    <div class="chart-box" id="chart-heatmap"></div>
  </div>
  <div class="chart-card">
    <div class="chart-title">🧠 Strategy Breakdown</div>
    <div class="chart-box" id="chart-strategy"></div>
  </div>
</div>

<script>
const BASE = "";
const chartConfig = {responsive: true, displayModeBar: false};
const overrideLayout = {
  paper_bgcolor: "#12182B", plot_bgcolor: "#0A0E1A",
  font: {color: "#FFFFFF"}, margin: {l: 50, r: 20, t: 40, b: 50}
};

async function loadChart(endpoint, elementId) {
  try {
    const res = await fetch(BASE + endpoint);
    if (!res.ok) throw new Error(res.statusText);
    const data = await res.json();
    const chart = data.chart;
    if (!chart) return;
    const layout = Object.assign({}, chart.layout, overrideLayout);
    Plotly.newPlot(elementId, chart.data, layout, chartConfig);
  } catch(e) {
    document.getElementById(elementId).innerHTML =
      '<p style="color:#ff6b35;padding:1rem;font-size:.85rem">Failed to load chart: ' + e.message + '</p>';
  }
}

function loadAll() {
  loadChart("/analytics/leaderboard-chart", "chart-leaderboard");
  loadChart("/analytics/score-distribution", "chart-scores");
  loadChart("/analytics/score-timeline", "chart-timeline");
  loadChart("/analytics/bowler-chart", "chart-bowler");
  loadChart("/analytics/field-heatmap", "chart-heatmap");
  loadChart("/analytics/strategy-breakdown", "chart-strategy");
}

window.addEventListener("DOMContentLoaded", loadAll);
</script>
</body>
</html>
"""
    return HTMLResponse(content=html)


# ── Status Endpoint ────────────────────────────────────────────────────────────

@router.get("/status")
def analytics_status():
    """Return availability status of analytics libraries."""
    return {
        "plotly_available": PLOTLY_AVAILABLE,
        "matplotlib_available": matplotlib_available(),
        "endpoints": [
            "/analytics/leaderboard-chart",
            "/analytics/score-distribution",
            "/analytics/score-timeline",
            "/analytics/bowler-chart",
            "/analytics/field-heatmap",
            "/analytics/strategy-breakdown",
            "/analytics/all-charts",
            "/analytics/static/leaderboard",
            "/analytics/static/score-history",
            "/analytics/static/bowler-economy",
            "/analytics/static/dashboard",
            "/analytics/dashboard",
        ],
    }
