"""
Flood risk evaluation and summary routes.
"""

from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.services.forecast_service import ForecastService
from src.services.severity_service import FloodSeverityService
from src.repositories.station_repository import StationRepository
from src.api.schemas import RiskAssessmentResponse, RiskSummaryResponse

router = APIRouter(prefix="/risk", tags=["Risk Classification"])
service = ForecastService.get_instance()


@router.get("/summary", response_model=RiskSummaryResponse)
def get_risk_summary(db: Session = Depends(get_db)):
    """Returns statewide and basin-wise counts across the 5 canonical risk categories."""
    stn_repo = StationRepository(db)
    stn_repo.seed_from_csv()
    stations = stn_repo.get_all()

    category_counts = {
        "Normal": 0,
        "Above Normal": 0,
        "Severe": 0,
        "Extreme": 0,
        "Threshold Unavailable": 0,
    }
    basin_distribution: Dict[str, Dict[str, int]] = {}

    for s in stations:
        basin = s.basin or "Other"
        if basin not in basin_distribution:
            basin_distribution[basin] = {
                "Normal": 0,
                "Above Normal": 0,
                "Severe": 0,
                "Extreme": 0,
                "Threshold Unavailable": 0,
            }

        try:
            forecast = service.forecast_for_station(s.station_id)
            sev = forecast.get("severity") or forecast.get("risk_level", "Threshold Unavailable")
        except Exception:
            sev = "Threshold Unavailable"

        if sev in category_counts:
            category_counts[sev] += 1
            basin_distribution[basin][sev] += 1
        else:
            category_counts["Threshold Unavailable"] += 1
            basin_distribution[basin]["Threshold Unavailable"] += 1

    return RiskSummaryResponse(
        category_counts=category_counts,
        basin_distribution=basin_distribution,
        disclaimer=FloodSeverityService.DISCLAIMER,
    )


@router.get("/{station_id}", response_model=RiskAssessmentResponse)
def get_station_risk(
    station_id: int = Path(..., ge=0, description="Station identifier"),
    db: Session = Depends(get_db),
):
    """Evaluates risk classification and civil defense advisory for a specific station."""
    try:
        res = service.forecast_for_station(station_id=station_id)
        return RiskAssessmentResponse(
            station_id=res["station_id"],
            station_name=res["station_name"],
            water_level_m=res["latest_observed_level_m"],
            warning_level_m=res["warning_level_m"],
            danger_level_m=res["danger_level_m"],
            hfl_m=res["hfl_m"],
            threshold_status=res["threshold_status"],
            threshold_source=res["threshold_source"],
            risk_level=res["risk_level"],
            risk_reason=res["risk_reason"],
            action_recommendation=res["action_recommendation"],
            disclaimer=res["disclaimer"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
