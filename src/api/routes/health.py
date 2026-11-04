"""
Health check route for FastAPI and database connectivity.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.database.connection import get_db
from src.services.prediction_service import PredictionService
from src.api.schemas import HealthResponse

router = APIRouter(prefix="", tags=["System"])


@router.get("/health", response_model=HealthResponse)
def get_health(db: Session = Depends(get_db)):
    """Verifies backend, database connectivity, and deep-learning model status."""
    db_connected = False
    try:
        db.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        db_connected = False

    pred_service = PredictionService.get_instance()
    model_loaded = pred_service.model is not None
    scalers_count = len(pred_service.scalers)

    return HealthResponse(
        status="ok" if (db_connected and model_loaded) else "degraded",
        model_loaded=model_loaded,
        scalers_count=scalers_count,
        data_source="SQLAlchemy / PostgreSQL / SQLite",
        database_connected=db_connected,
        background_scheduler_active=True,
    )
