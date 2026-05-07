# Analytics helper functions
"""
Analytics Module — Plotly Charts
=================================
Generates interactive Plotly charts from IPL decision database data.
All public functions return Plotly Figure objects (serialisable to JSON).
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


_DB_PATH = Path(__file__).parent.parent / "data" / "historical_matches.db"

COLORS = {
    "primary": "#FF6B35",
    "secondary": "#1E3A5F",
    "accent": "#FFD700",
    "success": "#00C851",
    "bg": "#0A0E1A",
    "text": "#FFFFFF",
}


def _query(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    if not _DB_PATH.exists():
        return []
    try:
        conn = sqlite3.connect(str(_DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
    except Exception:
        return []


def _apply_dark_template(fig) -> Any:
    fig.update_layout(
        plot_bgcolor=COLORS["bg"],
        paper_bgcolor="#12182B",
        font=dict(color=COLORS["text"], family="Segoe UI, sans-serif"),
        title_font=dict(size=18, color=COLORS["accent"]),
        legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0),
    )
    return fig


def get_leaderboard_chart(top_n: int = 10) -> Any:
    """Bar chart of top-N users by total points."""
    if not PLOTLY_AVAILABLE:
        return None
    rows = _query("SELECT username, points FROM users ORDER BY points DESC LIMIT ?", (top_n,))
    if not rows:
        rows = [
            {"username": "MS Dhoni Fan", "points": 950},
            {"username": "Bumrah Fan", "points": 880},
            {"username": "Kohli Fan", "points": 820},
            {"username": "Rohit Fan", "points": 790},
            {"username": "Jadeja Fan", "points": 740},
        ]
    usernames = [r["username"] for r in rows]
    points = [r["points"] for r in rows]
    colors = [COLORS["accent"] if p == max(points) else COLORS["primary"] for p in points]
    fig = go.Figure(go.Bar(
        x=usernames, y=points,
        marker=dict(color=colors, line=dict(color=COLORS["secondary"], width=1)),
        text=points, textposition="outside",
        hovertemplate="<b>%{x}</b><br>Points: %{y}<extra></extra>",
    ))
    fig.update_layout(title="🏆 IPL Fan Leaderboard", xaxis_title="Fan", yaxis_title="Total Points", showlegend=False)
    return _apply_dark_template(fig)


def get_score_distribution() -> Any:
    """Histogram of tactical decision scores."""
    if not PLOTLY_AVAILABLE:
        return None
    rows = _query("SELECT score FROM decisions WHERE score IS NOT NULL")
    scores = [r["score"] for r in rows if r.get("score") is not None]
    if not scores:
        import random; random.seed(42)
        scores = [max(0, min(100, round(random.gauss(65, 15), 1))) for _ in range(200)]
    fig = go.Figure(go.Histogram(
        x=scores, nbinsx=20,
        marker=dict(color=COLORS["primary"], line=dict(color=COLORS["secondary"], width=1)),
        hovertemplate="Score: %{x}<br>Count: %{y}<extra></extra>",
    ))
    fig.update_layout(title="📊 Fan Decision Score Distribution", xaxis_title="Tactical Score", yaxis_title="Submissions")
    return _apply_dark_template(fig)


def get_score_timeline() -> Any:
    """Line chart of average score per ball number."""
    if not PLOTLY_AVAILABLE:
        return None
    rows = _query(
        "SELECT ball_number, AVG(score) as avg_score, COUNT(*) as n "
        "FROM decisions WHERE score IS NOT NULL GROUP BY ball_number ORDER BY ball_number"
    )
    if not rows:
        rows = [{"ball_number": i, "avg_score": 55 + i * 0.8 + ((-1) ** i) * 3, "n": 10} for i in range(1, 21)]
    balls = [r["ball_number"] for r in rows]
    avgs = [round(r["avg_score"], 1) for r in rows]
    counts = [r["n"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=balls, y=avgs, mode="lines+markers", name="Avg Score",
        line=dict(color=COLORS["primary"], width=2),
        marker=dict(size=8, color=COLORS["accent"]),
        hovertemplate="Ball %{x}<br>Avg Score: %{y:.1f}<br>Submissions: %{text}<extra></extra>",
        text=counts,
    ))
    fig.add_vrect(x0=0.5, x1=6.5, fillcolor="rgba(0,188,212,0.07)", line_width=0,
                  annotation_text="Powerplay", annotation_position="top left",
                  annotation_font_color=COLORS["text"])
    fig.add_vrect(x0=14.5, x1=20.5, fillcolor="rgba(255,107,53,0.07)", line_width=0,
                  annotation_text="Death Overs", annotation_position="top right",
                  annotation_font_color=COLORS["text"])
    fig.update_layout(title="⚡ Avg Fan Score by Ball Number", xaxis_title="Ball Number", yaxis_title="Avg Score")
    return _apply_dark_template(fig)


def get_bowler_economy_chart() -> Any:
    """Horizontal bar chart of bowler economy rates."""
    if not PLOTLY_AVAILABLE:
        return None
    bowler_data = _get_bowler_stats()
    fig = go.Figure(go.Bar(
        x=[b["economy"] for b in bowler_data],
        y=[b["name"] for b in bowler_data],
        orientation="h",
        marker=dict(
            color=[COLORS["success"] if b["economy"] < 7.5 else COLORS["primary"] for b in bowler_data],
            line=dict(color=COLORS["secondary"], width=1),
        ),
        text=[f"{b['economy']:.1f}" for b in bowler_data],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Economy: %{x:.2f}<extra></extra>",
    ))
    fig.update_layout(title="🎯 IPL Bowler Economy Comparison", xaxis_title="Economy Rate (runs/over)", xaxis=dict(range=[0, 12]))
    return _apply_dark_template(fig)


def _get_bowler_stats() -> list[dict]:
    try:
        from ipl_agentic_coach.backend.app.cricket_data_service import cricket_data_service
        data = cricket_data_service.get_bowler_stats()
        if data:
            return [{"name": k, "economy": v.get("economy_rate", 8.0)} for k, v in list(data.items())[:10]]
    except Exception:
        pass
    return [
        {"name": "Jasprit Bumrah", "economy": 6.85},
        {"name": "Rashid Khan", "economy": 6.92},
        {"name": "Yuzvendra Chahal", "economy": 7.98},
        {"name": "Hardik Pandya", "economy": 8.42},
        {"name": "Mitchell Starc", "economy": 8.73},
        {"name": "Kagiso Rabada", "economy": 8.91},
        {"name": "Dwayne Bravo", "economy": 9.12},
        {"name": "Harshal Patel", "economy": 9.34},
    ]


def get_field_effectiveness_heatmap() -> Any:
    """Heatmap of field placement effectiveness by bowling style."""
    if not PLOTLY_AVAILABLE:
        return None
    z = [
        [0.85, 0.72, 0.65, 0.90, 0.78],
        [0.60, 0.88, 0.74, 0.65, 0.82],
        [0.75, 0.68, 0.92, 0.71, 0.69],
        [0.55, 0.79, 0.80, 0.60, 0.88],
    ]
    x_labels = ["Slip", "Cover", "Mid-Off", "Fine Leg", "Square Leg"]
    y_labels = ["Fast Pace", "Swing", "Spin", "Yorker"]
    fig = go.Figure(go.Heatmap(
        z=z, x=x_labels, y=y_labels,
        colorscale=[[0, "#1E3A5F"], [0.5, "#FF6B35"], [1, "#FFD700"]],
        text=[[f"{v:.0%}" for v in row] for row in z],
        texttemplate="%{text}",
        hovertemplate="Bowling: %{y}<br>Field: %{x}<br>Effectiveness: %{z:.0%}<extra></extra>",
        showscale=True, colorbar=dict(title="Effectiveness", tickformat=".0%"),
    ))
    fig.update_layout(title="🗺️ Field Placement Effectiveness Heatmap", xaxis_title="Field Zone", yaxis_title="Bowling Style")
    return _apply_dark_template(fig)


def get_strategy_breakdown() -> Any:
    """Donut chart of submitted decision styles."""
    if not PLOTLY_AVAILABLE:
        return None
    rows = _query("SELECT tactical_strategy, COUNT(*) as count FROM decisions GROUP BY tactical_strategy")
    if not rows:
        rows = [{"tactical_strategy": "aggressive", "count": 42}, {"tactical_strategy": "defensive", "count": 28}, {"tactical_strategy": "balanced", "count": 35}]
    labels = [r["tactical_strategy"].title() for r in rows]
    values = [r["count"] for r in rows]
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.5,
        marker=dict(colors=[COLORS["primary"], COLORS["secondary"], COLORS["accent"]]),
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(title="🧠 Fan Strategy Breakdown")
    return _apply_dark_template(fig)


def fig_to_json(fig) -> dict | None:
    """Convert Plotly figure to JSON-serialisable dict."""
    if fig is None or not PLOTLY_AVAILABLE:
        return None
    try:
        return json.loads(fig.to_json())
    except Exception:
        return None


def all_charts_json() -> dict[str, Any]:
    """Generate all charts and return as combined JSON dict."""
    return {
        "leaderboard": fig_to_json(get_leaderboard_chart()),
        "score_distribution": fig_to_json(get_score_distribution()),
        "score_timeline": fig_to_json(get_score_timeline()),
        "bowler_economy": fig_to_json(get_bowler_economy_chart()),
        "field_heatmap": fig_to_json(get_field_effectiveness_heatmap()),
        "strategy_breakdown": fig_to_json(get_strategy_breakdown()),
    }
