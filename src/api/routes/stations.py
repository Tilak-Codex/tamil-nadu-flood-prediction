"""
River monitoring station metadata and threshold routes.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.repositories.station_repository import StationRepository
from src.api.schemas import StationSummary

router = APIRouter(prefix="/stations", tags=["Stations"])


@router.get("", response_model=List[StationSummary])
def list_stations(db: Session = Depends(get_db)):
    """Returns all 35 Tamil Nadu monitoring stations with coordinates, basins, and CWC thresholds."""
    repo = StationRepository(db)
    repo.seed_from_csv()
    stations = repo.get_all()
    return [
        StationSummary(
            station_id=s.station_id,
            station_name=s.station_name,
            river=s.river,
            basin=s.basin,
            latitude=s.latitude,
            longitude=s.longitude,
            warning_level=s.warning_level,
            danger_level=s.danger_level,
            hfl=s.hfl,
            threshold_status=s.threshold_status,
            threshold_source=s.threshold_source,
        )
        for s in stations
    ]


@router.get("/{station_id}", response_model=StationSummary)
def get_station(
    station_id: int = Path(..., ge=0, description="Station identifier"),
    db: Session = Depends(get_db),
):
    """Returns metadata for a specific monitoring station."""
    repo = StationRepository(db)
    repo.seed_from_csv()
    stn = repo.get_by_id(station_id)
    if not stn:
        raise HTTPException(status_code=404, detail=f"Station ID {station_id} not found.")

    return StationSummary(
        station_id=stn.station_id,
        station_name=stn.station_name,
        river=stn.river,
        basin=stn.basin,
        latitude=stn.latitude,
        longitude=stn.longitude,
        warning_level=stn.warning_level,
        danger_level=stn.danger_level,
        hfl=stn.hfl,
        threshold_status=stn.threshold_status,
        threshold_source=stn.threshold_source,
    )
