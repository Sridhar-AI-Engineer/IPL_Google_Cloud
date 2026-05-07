from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from .cricket_data_service import cricket_data_service
from .database import DB_PATH


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _split_positions(value: str) -> list[str]:
    if not value:
        return []
    pieces = re.split(r"[,;+|]", value)
    cleaned = [piece.strip() for piece in pieces if piece.strip()]
    return cleaned


@dataclass
class TrainResult:
    model_path: Path
    metrics_path: Path
    samples: int
    rmse: float
    r2: float


class TacticalScoreMLModel:
    def __init__(self) -> None:
        self.project_root = Path(__file__).resolve().parents[2]
        self.model_dir = self.project_root / "data" / "models"
        self.model_path = self.model_dir / "tactical_score_model.joblib"
        self.metrics_path = self.model_dir / "tactical_score_metrics.json"
        self._model: Pipeline | None = None

        self._field_lookup = {
            _normalize_key(key): key
            for key in cricket_data_service._data_cache.get("field_effectiveness", {}).keys()
        }

    def _canonical_field_name(self, position: str) -> str:
        key = _normalize_key(position)
        return self._field_lookup.get(key, position)

    def _phase_from_ball(self, ball_number: int) -> str:
        if ball_number <= 6:
            return "powerplay"
        if ball_number <= 15:
            return "middle"
        return "death"

    def _build_feature_row(
        self,
        ball_number: int,
        field_placement: str,
        bowling_change: str,
        tactical_strategy: str,
    ) -> dict[str, Any]:
        phase = self._phase_from_ball(ball_number)
        positions = [self._canonical_field_name(p) for p in _split_positions(field_placement)]
        bowler_stats = cricket_data_service.get_bowler_stats(bowling_change)

        catch_probs: list[float] = []
        eff_pace: list[float] = []
        run_prevention: list[float] = []

        for position in positions:
            field_stats = cricket_data_service.get_field_effectiveness(position)
            if not field_stats:
                continue
            catch_probs.append(_safe_float(field_stats.get("catch_probability"), 0.0))
            eff_pace.append(_safe_float(field_stats.get("effectiveness_vs_pace"), 0.5))
            run_prevention.append(_safe_float(field_stats.get("run_prevention"), 0.0))

        phase_stats = bowler_stats.get(f"vs_{phase}", {})

        return {
            "ball_number": int(ball_number),
            "phase": phase,
            "field_placement": field_placement,
            "bowling_change": bowling_change,
            "tactical_strategy": tactical_strategy,
            "field_count": len(positions),
            "strategy_length": len(tactical_strategy or ""),
            "avg_catch_probability": float(np.mean(catch_probs)) if catch_probs else 0.0,
            "avg_eff_vs_pace": float(np.mean(eff_pace)) if eff_pace else 0.5,
            "avg_run_prevention": float(np.mean(run_prevention)) if run_prevention else 0.0,
            "bowler_economy": _safe_float(bowler_stats.get("economy"), 8.0),
            "bowler_wickets_per_match": _safe_float(bowler_stats.get("wickets_per_match"), 1.0),
            "bowler_yorker_accuracy": _safe_float(bowler_stats.get("yorker_accuracy"), 0.5),
            "bowler_dot_ball_percentage": _safe_float(bowler_stats.get("dot_ball_percentage"), 0.35),
            "phase_economy": _safe_float(phase_stats.get("economy"), _safe_float(bowler_stats.get("economy"), 8.0)),
            "phase_wickets": _safe_float(phase_stats.get("wickets"), _safe_float(bowler_stats.get("wickets_per_match"), 1.0)),
        }

    def load_training_dataset(self, db_path: Path | None = None) -> pd.DataFrame:
        target_db = db_path or DB_PATH
        connection = sqlite3.connect(target_db)
        try:
            decisions = pd.read_sql_query(
                """
                SELECT
                    ball_number,
                    field_placement,
                    bowling_change,
                    tactical_strategy,
                    score
                FROM decisions
                WHERE score IS NOT NULL
                """,
                connection,
            )

            historical = pd.read_sql_query(
                """
                SELECT
                    ball_number,
                    field_placement,
                    bowler AS bowling_change,
                    captain_move AS tactical_strategy,
                    expected_score AS score
                FROM historical_decisions
                WHERE expected_score IS NOT NULL
                """,
                connection,
            )
        finally:
            connection.close()

        dataset = pd.concat([decisions, historical], ignore_index=True)
        dataset = dataset.dropna(subset=["ball_number", "field_placement", "bowling_change", "score"])

        if dataset.empty:
            raise ValueError("No training data found in decisions/historical_decisions tables.")

        return dataset

    def build_features(self, dataset: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
        rows = []
        for record in dataset.to_dict(orient="records"):
            rows.append(
                self._build_feature_row(
                    ball_number=int(record["ball_number"]),
                    field_placement=str(record["field_placement"]),
                    bowling_change=str(record["bowling_change"]),
                    tactical_strategy=str(record.get("tactical_strategy") or ""),
                )
            )

        feature_df = pd.DataFrame(rows)
        y = dataset["score"].astype(float)
        return feature_df, y

    def _build_pipeline(self) -> Pipeline:
        numeric_features = [
            "ball_number",
            "field_count",
            "strategy_length",
            "avg_catch_probability",
            "avg_eff_vs_pace",
            "avg_run_prevention",
            "bowler_economy",
            "bowler_wickets_per_match",
            "bowler_yorker_accuracy",
            "bowler_dot_ball_percentage",
            "phase_economy",
            "phase_wickets",
        ]
        categorical_features = ["phase", "bowling_change", "field_placement"]

        preprocess = ColumnTransformer(
            transformers=[
                ("num", "passthrough", numeric_features),
                ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
                ("txt", TfidfVectorizer(max_features=150, ngram_range=(1, 2)), "tactical_strategy"),
            ]
        )

        model = RandomForestRegressor(
            n_estimators=250,
            random_state=42,
            min_samples_leaf=1,
            n_jobs=-1,
        )

        return Pipeline([("preprocess", preprocess), ("model", model)])

    def train(self, db_path: Path | None = None) -> TrainResult:
        dataset = self.load_training_dataset(db_path=db_path)
        X, y = self.build_features(dataset)

        self.model_dir.mkdir(parents=True, exist_ok=True)

        model = self._build_pipeline()
        if len(X) >= 8:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
            model.fit(X_train, y_train)
            predictions = model.predict(X_test)
            rmse = float(np.sqrt(mean_squared_error(y_test, predictions)))
            r2 = float(r2_score(y_test, predictions))
        else:
            model.fit(X, y)
            predictions = model.predict(X)
            rmse = float(np.sqrt(mean_squared_error(y, predictions)))
            r2 = float(r2_score(y, predictions)) if len(X) > 1 else 0.0

        joblib.dump(model, self.model_path)

        metrics = {
            "samples": int(len(X)),
            "rmse": rmse,
            "r2": r2,
            "model_type": "RandomForestRegressor",
            "features": list(X.columns),
        }
        self.metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

        self._model = model
        return TrainResult(
            model_path=self.model_path,
            metrics_path=self.metrics_path,
            samples=int(len(X)),
            rmse=rmse,
            r2=r2,
        )

    def load(self) -> None:
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        self._model = joblib.load(self.model_path)

    def predict_score(
        self,
        field_input: str,
        bowler_input: str,
        strategy_input: str,
        ball_number: int,
    ) -> float:
        if self._model is None:
            self.load()

        row = self._build_feature_row(
            ball_number=ball_number,
            field_placement=field_input,
            bowling_change=bowler_input,
            tactical_strategy=strategy_input,
        )
        X = pd.DataFrame([row])
        prediction = float(self._model.predict(X)[0])
        return max(0.0, min(1.0, prediction))

    def get_metrics(self) -> dict[str, Any]:
        if not self.metrics_path.exists():
            return {"status": "not_trained"}
        return json.loads(self.metrics_path.read_text(encoding="utf-8"))


ml_tactical_model = TacticalScoreMLModel()
