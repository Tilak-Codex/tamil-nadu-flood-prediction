"""
Observation endpoints for river telemetry and weather measurements.
"""

from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.repositories.observation_repository import ObservationRepository
from src.repositories.station_repository import StationRepository
from src.api.schemas import ObservationItem, StationObservationsResponse, WeatherObservationItem
from src.services.forecast_service import ForecastService

router = APIRouter(prefix="/observations", tags=["Observations"])
forecast_service = ForecastService.get_instance()


@router.get("/{station_id}", response_model=StationObservationsResponse)
def get_station_observations(
    station_id: int = Path(..., ge=0, description="Station identifier"),
    n: int = Query(48, ge=1, le=500, description="Number of recent observations"),
    db: Session = Depends(get_db),
):
    """Retrieves recent river water-level observations for a station."""
    obs_repo = ObservationRepository(db)
    stn_repo = StationRepository(db)
    stn_repo.seed_from_csv()

    records = obs_repo.get_history(station_id, limit=n)
    if not records:
        # Fallback to CSV data layer
        try:
            csv_obs = forecast_service.get_station_observations(station_id=station_id, n_recent=n)
            return StationObservationsResponse(station_id=station_id, count=len(csv_obs), observations=csv_obs)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"No observations found for station {station_id}: {e}")

    items = [
        ObservationItem(
            timestamp=r.timestamp.isoformat() if hasattr(r.timestamp, "isoformat") else str(r.timestamp),
            water_level=r.water_level,
            rainfall=r.rainfall,
            temperature=r.temperature,
            pressure=r.pressure,
            data_source=r.data_source,
            data_type=r.data_type,
            quality_status=r.quality_status,
            was_imputed=bool(r.was_imputed),
            is_outlier=bool(r.is_outlier),
        )
        for r in records
    ]
    return StationObservationsResponse(station_id=station_id, count=len(items), observations=items)


@router.get("/{station_id}/weather", response_model=List[WeatherObservationItem])
def get_station_weather_observations(
    station_id: int = Path(..., ge=0, description="Station identifier"),
    n: int = Query(48, ge=1, le=500, description="Number of recent records"),
    db: Session = Depends(get_db),
):
    """Retrieves recent weather observations (rainfall, temperature, pressure)."""
    obs_repo = ObservationRepository(db)
    weather_records = obs_repo.get_weather_history(station_id, limit=n)

    if not weather_records:
        # Fallback from CSV
        try:
            csv_obs = forecast_service.get_station_observations(station_id=station_id, n_recent=n)
            return [
                WeatherObservationItem(
                    timestamp=o["timestamp"],
                    rainfall=float(o.get("rainfall", 0.0) or 0.0),
                    temperature=float(o.get("temperature", 28.0) or 28.0),
                    pressure=float(o.get("pressure", 1010.0) or 1010.0),
                    data_source=o.get("data_source", "HISTORICAL_ENRICHED"),
                    data_type="HISTORICAL",
                    quality_status="VALID",
                )
                for o in csv_obs
            ]
        except Exception:
            return []

    return [
        WeatherObservationItem(
            timestamp=w.timestamp.isoformat() if hasattr(w.timestamp, "isoformat") else str(w.timestamp),
            rainfall=w.rainfall,
            temperature=w.temperature,
            pressure=w.pressure,
            relative_humidity=w.relative_humidity,
            data_source=w.data_source,
            data_type=w.data_type,
            quality_status=w.quality_status,
        )
        for w in weather_records
    ]
