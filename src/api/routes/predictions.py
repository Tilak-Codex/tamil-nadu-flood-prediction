"""
Predictions router for LSTM next-hour forecasting and persistence.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.services.forecast_service import ForecastService
from src.repositories.prediction_repository import PredictionRepository
from src.api.schemas import ForecastResponse, RunPredictionRequest, CustomForecastRequest

router = APIRouter(prefix="/predictions", tags=["Predictions"])
service = ForecastService.get_instance()


@router.get("/{station_id}", response_model=ForecastResponse)
def get_station_prediction(
    station_id: int = Path(..., ge=0, description="Station identifier"),
    db: Session = Depends(get_db),
):
    """
    Computes 1-hour ahead river water level forecast using the multi-station LSTM network.
    Compares against station-specific CWC thresholds and persists the inference into the database.
    """
    try:
        res = service.forecast_for_station(station_id=station_id)
        # Persist prediction to database
        pred_repo = PredictionRepository(db)
        pred_repo.add_prediction(
            station_id=station_id,
            target_timestamp=res["forecast_timestamp"],
            predicted_water_level=res["predicted_water_level_m"],
            latest_observed_level=res["latest_observed_level_m"],
            rate_of_change=res["rate_of_change_m_per_h"],
            severity=res["severity"] or res["risk_level"],
            severity_reason=res["severity_reason"] or res["risk_reason"],
            action_recommendation=res["action_recommendation"],
            model_version=res["model_version"],
        )
        return ForecastResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed for station {station_id}: {e}")


@router.post("/run", response_model=ForecastResponse)
def run_station_prediction(req: RunPredictionRequest, db: Session = Depends(get_db)):
    """Triggers an on-demand forecasting cycle for a station."""
    return get_station_prediction(station_id=req.station_id, db=db)


@router.get("/history/{station_id}")
def get_prediction_history(
    station_id: int = Path(..., ge=0),
    limit: int = Query(24, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Retrieves recent stored model predictions for a station from the database."""
    pred_repo = PredictionRepository(db)
    preds = pred_repo.get_recent_by_station(station_id=station_id, limit=limit)
    return [
        {
            "id": p.id,
            "station_id": p.station_id,
            "generation_timestamp": p.generation_timestamp.isoformat(),
            "target_timestamp": p.target_timestamp.isoformat(),
            "forecast_horizon_hours": p.forecast_horizon_hours,
            "predicted_water_level": p.predicted_water_level,
            "latest_observed_level": p.latest_observed_level,
            "rate_of_change": p.rate_of_change,
            "severity": p.severity,
            "severity_reason": p.severity_reason,
            "action_recommendation": p.action_recommendation,
            "model_version": p.model_version,
        }
        for p in preds
    ]
