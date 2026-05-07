# Visualization helper functions
"""
Visualizations Module — Matplotlib Charts
==========================================
Generates static IPL charts using Matplotlib.
Returns base64-encoded PNG data URIs for HTML/API embedding.
"""

from __future__ import annotations

import base64
import io
import random
import sqlite3
from pathlib import Path
from typing import Any

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

_DB_PATH = Path(__file__).parent.parent / "data" / "historical_matches.db"

_BG = "#0A0E1A"; _PANEL = "#12182B"; _ORANGE = "#FF6B35"
_GOLD = "#FFD700"; _BLUE = "#1E3A5F"; _WHITE = "#FFFFFF"; _GREEN = "#00C851"


def _query(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    if not _DB_PATH.exists():
        return []
    try:
        conn = sqlite3.connect(str(_DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor(); cur.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]; conn.close()
        return rows
    except Exception:
        return []


def _fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=120, facecolor=_BG, edgecolor="none")
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return f"data:image/png;base64,{encoded}"


def _dark(ax, fig) -> None:
    fig.patch.set_facecolor(_BG); ax.set_facecolor(_PANEL)
    ax.tick_params(colors=_WHITE, labelsize=9)
    ax.xaxis.label.set_color(_WHITE); ax.yaxis.label.set_color(_WHITE)
    ax.title.set_color(_GOLD)
    for spine in ax.spines.values(): spine.set_edgecolor(_BLUE)


def plot_leaderboard_bar(top_n: int = 10) -> str:
    """Horizontal bar chart of top-N fans by points (base64 PNG)."""
    if not MATPLOTLIB_AVAILABLE: return ""
    rows = _query("SELECT username, points FROM users ORDER BY points DESC LIMIT ?", (top_n,))
    if not rows:
        rows = [{"username": n, "points": p} for n, p in
                [("MS Dhoni Fan", 950), ("Bumrah Fan", 880), ("Kohli Fan", 820), ("Rohit Fan", 790), ("Jadeja Fan", 740)]]
    names = [r["username"] for r in rows][::-1]
    points = [r["points"] for r in rows][::-1]
    colors = [_GOLD if p == max(points) else _ORANGE for p in points]
    fig, ax = plt.subplots(figsize=(9, max(4, len(names) * 0.55)))
    bars = ax.barh(names, points, color=colors, edgecolor=_BLUE, linewidth=0.8)
    for bar, pt in zip(bars, points):
        ax.text(pt + max(points) * 0.01, bar.get_y() + bar.get_height() / 2,
                str(pt), va="center", ha="left", color=_WHITE, fontsize=9)
    ax.set_xlabel("Total Points"); ax.set_title("🏆 IPL Fan Leaderboard", fontsize=14, fontweight="bold")
    _dark(ax, fig); return _fig_to_base64(fig)


def plot_score_history() -> str:
    """Line chart of average decision score over ball number (base64 PNG)."""
    if not MATPLOTLIB_AVAILABLE: return ""
    rows = _query(
        "SELECT ball_number, AVG(score) as avg_score FROM decisions WHERE score IS NOT NULL "
        "GROUP BY ball_number ORDER BY ball_number"
    )
    if not rows:
        random.seed(99)
        rows = [{"ball_number": i, "avg_score": 55 + i * 0.9 + random.gauss(0, 3)} for i in range(1, 21)]
    balls = [r["ball_number"] for r in rows]; avgs = [r["avg_score"] for r in rows]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(balls, avgs, color=_ORANGE, linewidth=2, marker="o", markersize=5, markerfacecolor=_GOLD, markeredgewidth=0)
    ax.fill_between(balls, avgs, alpha=0.15, color=_ORANGE)
    ax.axvspan(0.5, 6.5, alpha=0.06, color="#00BCD4"); ax.axvspan(14.5, max(balls) + 0.5, alpha=0.06, color=_ORANGE)
    ax.set_xlabel("Ball Number"); ax.set_ylabel("Avg Score")
    ax.set_title("⚡ Average Fan Score by Ball Number", fontsize=13, fontweight="bold")
    _dark(ax, fig); return _fig_to_base64(fig)


def plot_bowler_economy() -> str:
    """Bar chart of IPL bowler economy rates (base64 PNG)."""
    if not MATPLOTLIB_AVAILABLE: return ""
    bowlers = [("Jasprit Bumrah", 6.85), ("Rashid Khan", 6.92), ("Yuzvendra Chahal", 7.98),
               ("Hardik Pandya", 8.42), ("Mitchell Starc", 8.73), ("Kagiso Rabada", 8.91),
               ("Dwayne Bravo", 9.12), ("Harshal Patel", 9.34)]
    names = [b[0] for b in bowlers]; economies = [b[1] for b in bowlers]
    colors = [_GREEN if e < 7.5 else _ORANGE for e in economies]
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(names, economies, color=colors, edgecolor=_BLUE, linewidth=0.8)
    ax.axhline(y=7.5, color=_GOLD, linestyle="--", linewidth=1, alpha=0.7, label="Economy Threshold")
    for bar, eco in zip(bars, economies):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                f"{eco:.2f}", ha="center", va="bottom", color=_WHITE, fontsize=8)
    ax.set_ylabel("Economy Rate (runs/over)")
    ax.set_title("🎯 IPL Bowler Economy Comparison", fontsize=13, fontweight="bold")
    ax.set_xticklabels(names, rotation=30, ha="right", fontsize=8)
    ax.legend(facecolor=_PANEL, edgecolor=_BLUE, labelcolor=_WHITE)
    _dark(ax, fig); return _fig_to_base64(fig)


def plot_dashboard_overview() -> str:
    """2×2 multi-panel Matplotlib dashboard (base64 PNG)."""
    if not MATPLOTLIB_AVAILABLE: return ""
    random.seed(42)
    fig = plt.figure(figsize=(14, 9)); fig.patch.set_facecolor(_BG)
    gs = GridSpec(2, 2, figure=fig, hspace=0.45, wspace=0.35)

    ax1 = fig.add_subplot(gs[0, 0])
    scores = [max(0, min(100, round(random.gauss(65, 15), 1))) for _ in range(200)]
    ax1.hist(scores, bins=20, color=_ORANGE, edgecolor=_BLUE, linewidth=0.6)
    ax1.set_title("Score Distribution", fontsize=11, fontweight="bold"); ax1.set_xlabel("Score"); ax1.set_ylabel("Count")
    _dark(ax1, fig)

    ax2 = fig.add_subplot(gs[0, 1]); balls = list(range(1, 21))
    avgs = [55 + b * 0.9 + random.gauss(0, 2) for b in balls]
    ax2.plot(balls, avgs, color=_ORANGE, linewidth=1.8, marker="o", markersize=4, markerfacecolor=_GOLD, markeredgewidth=0)
    ax2.fill_between(balls, avgs, alpha=0.1, color=_ORANGE)
    ax2.set_title("Score by Ball #", fontsize=11, fontweight="bold"); ax2.set_xlabel("Ball"); ax2.set_ylabel("Avg Score")
    _dark(ax2, fig)

    ax3 = fig.add_subplot(gs[1, 0])
    wedges, _, autotexts = ax3.pie(
        [42, 35, 28], labels=["Aggressive", "Balanced", "Defensive"],
        colors=[_ORANGE, _GOLD, _BLUE], autopct="%1.0f%%", startangle=140,
        textprops={"color": _WHITE, "fontsize": 9}, wedgeprops={"edgecolor": _BG, "linewidth": 1.5},
    )
    for at in autotexts: at.set_color(_WHITE)
    ax3.set_title("Strategy Breakdown", fontsize=11, fontweight="bold", color=_GOLD)

    ax4 = fig.add_subplot(gs[1, 1])
    names_s = ["Bumrah", "Rashid", "Chahal", "Pandya", "Starc"]; ecnm = [6.85, 6.92, 7.98, 8.42, 8.73]
    ax4.barh(names_s, ecnm, color=[_GREEN if e < 7.5 else _ORANGE for e in ecnm], edgecolor=_BLUE, linewidth=0.7)
    ax4.axvline(7.5, color=_GOLD, linestyle="--", linewidth=1, alpha=0.7)
    ax4.set_title("Bowler Economy", fontsize=11, fontweight="bold"); ax4.set_xlabel("Economy Rate")
    _dark(ax4, fig)

    fig.suptitle("🏏 IPL Fan Coach — Analytics Dashboard", fontsize=16, fontweight="bold", color=_GOLD, y=1.01)
    return _fig_to_base64(fig)


def is_available() -> bool:
    return MATPLOTLIB_AVAILABLE
