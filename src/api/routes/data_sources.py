"""
Data source health, accessibility tracking, and manual ingestion routes.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.repositories.data_source_repository import DataSourceRepository
from src.services.data_ingestion import DataIngestionService
from src.api.schemas import DataSourceStatusResponse, DataRefreshResponse

router = APIRouter(prefix="/data-sources", tags=["Data Sources"])


@router.get("", response_model=List[DataSourceStatusResponse])
def get_data_sources_status(db: Session = Depends(get_db)):
    """Returns connectivity, authorization status, and telemetry updates across all monitoring sources."""
    repo = DataSourceRepository(db)
    repo.initialize_default_sources()
    sources = repo.get_all()
    return [
        DataSourceStatusResponse(
            source_name=s.source_name,
            status=s.status,
            last_successful_fetch=s.last_successful_fetch.isoformat() if s.last_successful_fetch else None,
            latest_observation_time=s.latest_observation_time.isoformat() if s.latest_observation_time else None,
            error_details=s.error_details,
            update_frequency=s.update_frequency,
            api_endpoint=s.api_endpoint,
            notes=s.notes,
        )
        for s in sources
    ]


@router.post("/refresh", response_model=DataRefreshResponse)
async def refresh_data_sources(db: Session = Depends(get_db)):
    """Executes live refresh cycle for Open-Meteo, CWC, IMD, and Tamil Nadu portals."""
    ingestion_service = DataIngestionService()
    try:
        results = await ingestion_service.refresh_all_sources(db=db)
        return DataRefreshResponse(
            status="SUCCESS",
            refreshed_at=results["refreshed_at"],
            stations_processed=results["stations_processed"],
            observations_added_or_updated=results["observations_added_or_updated"],
            errors=results.get("errors", []),
            source_statuses=results.get("source_statuses", {}),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refresh failed: {e}")
