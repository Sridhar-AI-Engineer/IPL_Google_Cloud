from __future__ import annotations

from ipl_agentic_coach.backend.app.ml_model import ml_tactical_model


if __name__ == "__main__":
    result = ml_tactical_model.train()
    print("✅ Tactical ML model trained")
    print(f"Samples: {result.samples}")
    print(f"RMSE: {result.rmse:.4f}")
    print(f"R2: {result.r2:.4f}")
    print(f"Model: {result.model_path}")
    print(f"Metrics: {result.metrics_path}")
