from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..ml_model import ml_tactical_model
from ..schemas import DecisionEvaluate

router = APIRouter()


@router.post("/train")
def train_tactical_model():
    try:
        result = ml_tactical_model.train()
        return {
            "status": "trained",
            "samples": result.samples,
            "rmse": result.rmse,
            "r2": result.r2,
            "model_path": str(result.model_path),
            "metrics_path": str(result.metrics_path),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Model training failed: {exc}") from exc


@router.post("/predict")
def predict_tactical_score(payload: DecisionEvaluate):
    try:
        score = ml_tactical_model.predict_score(
            field_input=payload.field_input,
            bowler_input=payload.bowler_input,
            strategy_input=payload.strategy_input,
            ball_number=payload.ball_number,
        )
        return {
            "predicted_score": score,
            "inputs": {
                "field_input": payload.field_input,
                "bowler_input": payload.bowler_input,
                "strategy_input": payload.strategy_input,
                "ball_number": payload.ball_number,
            },
            "model_metrics": ml_tactical_model.get_metrics(),
        }
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="ML model not trained yet. Call /ml/train first.",
        ) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}") from exc


@router.get("/metrics")
def model_metrics():
    return ml_tactical_model.get_metrics()
