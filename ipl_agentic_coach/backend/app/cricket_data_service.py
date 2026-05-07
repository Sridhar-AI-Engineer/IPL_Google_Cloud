"""
Cricket Data Service - Provides dynamic cricket statistics for AI analysis.
Loads real IPL data from local cache and provides tactical insights.
"""

from __future__ import annotations

import json
import os
import time
from threading import Lock
from pathlib import Path
from typing import Any


class CricketDataService:
    """Manages cricket statistics and historical data for tactical analysis."""

    _instance = None
    _data_cache: dict[str, Any] = {}

    def __new__(cls) -> CricketDataService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._lock = Lock()
            cls._instance._refresh_interval_seconds = 30
            cls._instance._last_refresh_check = 0.0
            cls._instance._data_files = {}
            cls._instance._file_mtimes = {}
            cls._instance._load_cricket_data()
        return cls._instance

    def _load_cricket_data(self) -> None:
        """Load cricket statistics from data directory."""
        data_dir = Path(__file__).parent.parent.parent / "data"
        self._data_files = {
            "bowlers": data_dir / "ipl_bowler_stats.json",
            "field_effectiveness": data_dir / "field_effectiveness.json",
            "matchups": data_dir / "batsman_bowler_matchups.json",
        }
        
        # Load bowler statistics
        bowler_file = self._data_files["bowlers"]
        if bowler_file.exists():
            with open(bowler_file) as f:
                self._data_cache["bowlers"] = json.load(f)
            self._file_mtimes["bowlers"] = bowler_file.stat().st_mtime
        else:
            self._data_cache["bowlers"] = self._get_default_bowler_stats()

        # Load field effectiveness data
        field_file = self._data_files["field_effectiveness"]
        if field_file.exists():
            with open(field_file) as f:
                self._data_cache["field_effectiveness"] = json.load(f)
            self._file_mtimes["field_effectiveness"] = field_file.stat().st_mtime
        else:
            self._data_cache["field_effectiveness"] = self._get_default_field_stats()

        # Load batsman vs bowler history
        history_file = self._data_files["matchups"]
        if history_file.exists():
            with open(history_file) as f:
                self._data_cache["matchups"] = json.load(f)
            self._file_mtimes["matchups"] = history_file.stat().st_mtime
        else:
            self._data_cache["matchups"] = {}

    def _maybe_refresh_data(self) -> None:
        now = time.time()
        if now - self._last_refresh_check < self._refresh_interval_seconds:
            return

        with self._lock:
            if now - self._last_refresh_check < self._refresh_interval_seconds:
                return

            for key, file_path in self._data_files.items():
                if not file_path.exists():
                    continue
                current_mtime = file_path.stat().st_mtime
                last_mtime = self._file_mtimes.get(key)
                if last_mtime is None or current_mtime > last_mtime:
                    self._load_cricket_data()
                    break

            self._last_refresh_check = now

    @staticmethod
    def _get_default_bowler_stats() -> dict[str, Any]:
        """Return realistic IPL bowler statistics."""
        return {
            "Pat Cummins": {
                "economy": 8.2,
                "wickets_per_match": 1.2,
                "death_overs_economy": 9.8,
                "yorker_accuracy": 0.68,
                "dot_ball_percentage": 0.35,
                "average_dot_runs": 0.75,
                "strong_zones": ["yorker", "back-of-length"],
                "weak_zones": ["full-length", "wide-yorker"],
                "vs_powerplay": {"economy": 7.5, "wickets": 0.8},
                "vs_middle": {"economy": 8.1, "wickets": 1.3},
                "vs_death": {"economy": 9.8, "wickets": 1.5},
            },
            "Bhuvneshwar Kumar": {
                "economy": 7.1,
                "wickets_per_match": 1.4,
                "death_overs_economy": 8.5,
                "yorker_accuracy": 0.71,
                "dot_ball_percentage": 0.42,
                "average_dot_runs": 0.65,
                "strong_zones": ["swing", "seam"],
                "weak_zones": ["short-pitch"],
                "vs_powerplay": {"economy": 5.8, "wickets": 1.1},
                "vs_middle": {"economy": 7.2, "wickets": 1.5},
                "vs_death": {"economy": 8.5, "wickets": 1.2},
            },
            "Shaheen Afridi": {
                "economy": 8.4,
                "wickets_per_match": 1.6,
                "death_overs_economy": 9.2,
                "yorker_accuracy": 0.65,
                "dot_ball_percentage": 0.38,
                "average_dot_runs": 0.82,
                "strong_zones": ["yorker", "intimidation"],
                "weak_zones": ["variations"],
                "vs_powerplay": {"economy": 8.1, "wickets": 1.8},
                "vs_middle": {"economy": 8.3, "wickets": 1.4},
                "vs_death": {"economy": 9.2, "wickets": 1.5},
            },
            "Jaydev Unadkat": {
                "economy": 8.0,
                "wickets_per_match": 1.1,
                "death_overs_economy": 10.2,
                "yorker_accuracy": 0.62,
                "dot_ball_percentage": 0.36,
                "average_dot_runs": 0.78,
                "strong_zones": ["pace-off", "variations"],
                "weak_zones": ["yorker"],
                "vs_powerplay": {"economy": 7.8, "wickets": 0.9},
                "vs_middle": {"economy": 7.9, "wickets": 1.2},
                "vs_death": {"economy": 10.2, "wickets": 1.0},
            },
            "Hasan Ali": {
                "economy": 8.6,
                "wickets_per_match": 1.3,
                "death_overs_economy": 9.5,
                "yorker_accuracy": 0.64,
                "dot_ball_percentage": 0.34,
                "average_dot_runs": 0.85,
                "strong_zones": ["yorker", "slower-ball"],
                "weak_zones": ["full-length"],
                "vs_powerplay": {"economy": 8.1, "wickets": 1.1},
                "vs_middle": {"economy": 8.5, "wickets": 1.4},
                "vs_death": {"economy": 9.5, "wickets": 1.4},
            },
            "Mayank Markande": {
                "economy": 7.8,
                "wickets_per_match": 1.5,
                "death_overs_economy": 8.1,
                "yorker_accuracy": 0.58,
                "dot_ball_percentage": 0.41,
                "average_dot_runs": 0.68,
                "strong_zones": ["googly", "flipper"],
                "weak_zones": ["sweep-balls"],
                "vs_powerplay": {"economy": 7.2, "wickets": 1.2},
                "vs_middle": {"economy": 7.6, "wickets": 1.8},
                "vs_death": {"economy": 8.1, "wickets": 1.2},
            },
            "Abhishek Sharma": {
                "economy": 7.5,
                "wickets_per_match": 1.2,
                "death_overs_economy": 8.0,
                "yorker_accuracy": 0.60,
                "dot_ball_percentage": 0.39,
                "average_dot_runs": 0.72,
                "strong_zones": ["arm-ball", "quicker"],
                "weak_zones": ["boundary-ball"],
                "vs_powerplay": {"economy": 7.1, "wickets": 1.0},
                "vs_middle": {"economy": 7.4, "wickets": 1.3},
                "vs_death": {"economy": 8.0, "wickets": 1.1},
            },
            "Washington Sundar": {
                "economy": 7.2,
                "wickets_per_match": 1.4,
                "death_overs_economy": 7.8,
                "yorker_accuracy": 0.61,
                "dot_ball_percentage": 0.43,
                "average_dot_runs": 0.66,
                "strong_zones": ["carrom-ball", "off-spin"],
                "weak_zones": ["short-pitched"],
                "vs_powerplay": {"economy": 6.8, "wickets": 1.1},
                "vs_middle": {"economy": 7.0, "wickets": 1.6},
                "vs_death": {"economy": 7.8, "wickets": 1.3},
            },
        }

    @staticmethod
    def _get_default_field_stats() -> dict[str, Any]:
        """Return field effectiveness statistics."""
        return {
            "Slip": {
                "catch_probability": 0.18,
                "effectiveness_vs_pace": 0.85,
                "effectiveness_vs_spin": 0.45,
                "best_for": ["edges", "thick-edges"],
                "placement_depth": "close",
            },
            "Gully": {
                "catch_probability": 0.16,
                "effectiveness_vs_pace": 0.78,
                "effectiveness_vs_spin": 0.52,
                "best_for": ["cuts", "slashed-drives"],
                "placement_depth": "close",
            },
            "Point": {
                "catch_probability": 0.14,
                "effectiveness_vs_pace": 0.72,
                "effectiveness_vs_spin": 0.68,
                "best_for": ["cuts", "drives"],
                "placement_depth": "close",
            },
            "Cover": {
                "catch_probability": 0.12,
                "effectiveness_vs_pace": 0.75,
                "effectiveness_vs_spin": 0.70,
                "best_for": ["drives", "cover-shots"],
                "placement_depth": "close",
            },
            "Mid-Off": {
                "catch_probability": 0.10,
                "effectiveness_vs_pace": 0.68,
                "effectiveness_vs_spin": 0.75,
                "best_for": ["straight-drives"],
                "placement_depth": "close",
            },
            "Mid-On": {
                "catch_probability": 0.11,
                "effectiveness_vs_pace": 0.65,
                "effectiveness_vs_spin": 0.72,
                "best_for": ["on-drives", "flicks"],
                "placement_depth": "close",
            },
            "Midwicket": {
                "catch_probability": 0.15,
                "effectiveness_vs_pace": 0.70,
                "effectiveness_vs_spin": 0.68,
                "best_for": ["pulls", "flicks"],
                "placement_depth": "close",
            },
            "Square Leg": {
                "catch_probability": 0.13,
                "effectiveness_vs_pace": 0.68,
                "effectiveness_vs_spin": 0.65,
                "best_for": ["pulls", "leg-side shots"],
                "placement_depth": "close",
            },
            "Fine Leg": {
                "catch_probability": 0.09,
                "effectiveness_vs_pace": 0.55,
                "effectiveness_vs_spin": 0.48,
                "best_for": ["glances", "fine-shots"],
                "placement_depth": "fine",
            },
            "Long On": {
                "catch_probability": 0.08,
                "effectiveness_vs_pace": 0.62,
                "effectiveness_vs_spin": 0.58,
                "best_for": ["lofted-shots"],
                "placement_depth": "deep",
            },
            "Long Off": {
                "catch_probability": 0.08,
                "effectiveness_vs_pace": 0.65,
                "effectiveness_vs_spin": 0.60,
                "best_for": ["lofted-shots"],
                "placement_depth": "deep",
            },
            "Deep Midwicket": {
                "catch_probability": 0.10,
                "effectiveness_vs_pace": 0.72,
                "effectiveness_vs_spin": 0.68,
                "best_for": ["pull-boundary", "big-hits"],
                "placement_depth": "deep",
            },
            "Deep Cover": {
                "catch_probability": 0.09,
                "effectiveness_vs_pace": 0.70,
                "effectiveness_vs_spin": 0.65,
                "best_for": ["drive-boundary"],
                "placement_depth": "deep",
            },
            "Third Man": {
                "catch_probability": 0.11,
                "effectiveness_vs_pace": 0.78,
                "effectiveness_vs_spin": 0.35,
                "best_for": ["edges", "fine-shots"],
                "placement_depth": "fine",
            },
        }

    def get_bowler_stats(self, bowler_name: str) -> dict[str, Any]:
        """Get performance statistics for a specific bowler."""
        self._maybe_refresh_data()
        bowlers = self._data_cache.get("bowlers", {})
        return bowlers.get(bowler_name, self._get_generic_bowler_profile())

    def get_field_effectiveness(self, position: str) -> dict[str, Any]:
        """Get effectiveness data for a field position."""
        self._maybe_refresh_data()
        field_data = self._data_cache.get("field_effectiveness", {})
        return field_data.get(position, {})

    def get_batsman_vs_bowler(self, batsman: str, bowler: str) -> dict[str, Any]:
        """Get historical matchup data between batsman and bowler."""
        self._maybe_refresh_data()
        matchups = self._data_cache.get("matchups", {})
        key = f"{batsman}_vs_{bowler}"
        return matchups.get(key, {})

    def get_field_combination_score(self, positions: list[str], context: str = "death") -> float:
        """
        Score a field combination based on context (powerplay, middle, death).
        Returns 0.0 to 1.0 score.
        """
        if not positions:
            return 0.3

        field_data = self._data_cache.get("field_effectiveness", {})
        
        # Calculate base effectiveness
        total_effectiveness = 0.0
        for pos in positions:
            pos_data = field_data.get(pos, {})
            if context == "powerplay":
                eff = pos_data.get("effectiveness_vs_pace", 0.5)
            elif context == "death":
                eff = pos_data.get("effectiveness_vs_pace", 0.5)
            else:
                eff = pos_data.get("effectiveness_vs_spin", 0.5)
            total_effectiveness += eff

        avg_effectiveness = total_effectiveness / len(positions) if positions else 0.5
        
        # Bonus for well-distributed field
        unique_depths = set(field_data.get(pos, {}).get("placement_depth", "close") for pos in positions)
        depth_bonus = min(0.15, len(unique_depths) * 0.05)
        
        final_score = min(1.0, (avg_effectiveness + depth_bonus) / (1 + depth_bonus))
        return round(final_score, 3)

    @staticmethod
    def _get_generic_bowler_profile() -> dict[str, Any]:
        """Return generic profile for unknown bowlers."""
        return {
            "economy": 8.0,
            "wickets_per_match": 1.2,
            "death_overs_economy": 9.0,
            "yorker_accuracy": 0.60,
            "dot_ball_percentage": 0.37,
            "average_dot_runs": 0.77,
            "strong_zones": ["yorker", "slower-ball"],
            "weak_zones": ["full-length", "wide-slower"],
            "vs_powerplay": {"economy": 7.5, "wickets": 1.0},
            "vs_middle": {"economy": 8.0, "wickets": 1.3},
            "vs_death": {"economy": 9.0, "wickets": 1.2},
        }

    def get_tactical_insights(
        self,
        bowler: str,
        field_positions: list[str],
        phase: str = "death",
    ) -> dict[str, Any]:
        """Generate tactical insights combining bowler stats and field data."""
        bowler_stats = self.get_bowler_stats(bowler)
        field_score = self.get_field_combination_score(field_positions, phase)
        
        # Get phase-specific stats
        phase_key = f"vs_{phase}"
        phase_stats = bowler_stats.get(phase_key, {"economy": 8.0, "wickets": 1.2})
        
        insights = {
            "bowler": bowler,
            "bowler_economy": bowler_stats.get("economy", 8.0),
            "bowler_wickets_per_match": bowler_stats.get("wickets_per_match", 1.2),
            "phase": phase,
            "phase_economy": phase_stats.get("economy", 8.0),
            "phase_wickets": phase_stats.get("wickets", 1.2),
            "field_score": field_score,
            "field_positions": field_positions,
            "bowler_strong_zones": bowler_stats.get("strong_zones", []),
            "bowler_weak_zones": bowler_stats.get("weak_zones", []),
            "recommended_bowling_area": self._recommend_bowling_area(bowler_stats, field_positions),
        }
        return insights

    @staticmethod
    def _recommend_bowling_area(bowler_stats: dict, field_positions: list[str]) -> str:
        """Recommend optimal bowling area based on bowler strengths and field."""
        strong_zones = bowler_stats.get("strong_zones", [])
        
        if "yorker" in strong_zones and field_positions:
            return "yorker - Use block-hole line to prevent boundaries"
        elif "slower-ball" in strong_zones:
            return "slower-ball - Mix pace to disrupt rhythm"
        elif "variations" in strong_zones:
            return "variations - Change pace and length frequently"
        else:
            return "consistent-lines - Maintain nagging length with dot-ball focus"


# Singleton instance
cricket_data_service = CricketDataService()
