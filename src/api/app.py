"""
FastAPI application for AI-Based Flood Prediction & Decision Support System for Tamil Nadu.
Exposes clean REST endpoints connecting the CSV data access layer,
trained deep-learning models, and deterministic risk classification engines.
"""

from pathlib import Path as FilePath
from typing import List
import pandas as pd
from fastapi import FastAPI, HTTPException, Path, Query, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from src.database.connection import get_db, init_db
from src.api.schemas import (
    HealthResponse,
    StationSummary,
    StationObservationsResponse,
    ForecastResponse,
    RiskAssessmentResponse,
    ThresholdResponse,
    MetricItem,
    CustomForecastRequest,
)
from src.data.validator import DataValidationError
from src.services.forecast_service import ForecastService

# Import modular API routers
from src.api.routes import stations, observations, predictions, risk, alerts, dashboard, data_sources, health

app = FastAPI(
    title="Tamil Nadu Flood Prediction & Decision Support System API",
    description="Research AI system for river water level forecasting, CWC threshold evaluation, and emergency decision support.",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration for React frontend development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register modular sub-routers with /api prefix
app.include_router(stations.router, prefix="/api")
app.include_router(observations.router, prefix="/api")
app.include_router(predictions.router, prefix="/api")
app.include_router(risk.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(data_sources.router, prefix="/api")
app.include_router(health.router, prefix="/api")

# Static frontend directory mount (serves React build or index.html)
REACT_DIST_DIR = FilePath(__file__).resolve().parent.parent.parent / "frontend" / "dist"
STATIC_DIR = FilePath(__file__).resolve().parent / "static"

if REACT_DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(REACT_DIST_DIR / "assets")), name="assets")
elif STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

service = ForecastService.get_instance()


@app.on_event("startup")
def startup_event():
    """Initializes tables on startup."""
    try:
        init_db()
    except Exception as e:
        print(f"[Startup Warning] DB init error: {e}")


@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
def serve_dashboard():
    """Serves the interactive Tamil Nadu Flood Risk & Warning Map Frontend."""
    if REACT_DIST_DIR.exists() and (REACT_DIST_DIR / "index.html").exists():
        return FileResponse(REACT_DIST_DIR / "index.html")
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h2>Frontend is loading. Please verify frontend dist or static/index.html</h2>")


# ============================================================================
# Backwards-Compatible Top-Level Endpoints
# ============================================================================

@app.get("/map-summary", response_model=List[ForecastResponse], tags=["Frontend"])
def get_map_summary():
    """Returns real-time predictions, coordinates, and CWC risk evaluations for all 35 stations."""
    try:
        return service.get_all_stations_forecast_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """Health check verifying model loading and scaler availability."""
    return HealthResponse(
        status="ok",
        model_loaded=service.model is not None,
        scalers_count=len(service.scalers),
        data_source="CSV",
        database_connected=True,
    )


@app.get("/stations", response_model=List[StationSummary], tags=["Stations"])
def get_all_stations():
    """Returns metadata, geographic coordinates, and threshold configuration for all stations."""
    try:
        return service.get_stations_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stations/{station_id}", response_model=StationSummary, tags=["Stations"])
def get_station_by_id(station_id: int = Path(..., ge=0, description="Station identifier")):
    """Returns metadata for a specific river monitoring station."""
    stations_list = service.get_stations_summary()
    for s in stations_list:
        if s["station_id"] == station_id:
            return s
    raise HTTPException(status_code=404, detail=f"Station ID {station_id} not found.")


@app.get("/observations/{station_id}", response_model=StationObservationsResponse, tags=["Data"])
def get_observations(
    station_id: int = Path(..., ge=0),
    n: int = Query(24, ge=1, le=500, description="Number of recent observations to retrieve"),
):
    """Retrieves recent real-world water level observations for a station from CSV storage."""
    try:
        obs = service.get_station_observations(station_id=station_id, n_recent=n)
        return StationObservationsResponse(station_id=station_id, count=len(obs), observations=obs)
    except DataValidationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/forecast/{station_id}", response_model=ForecastResponse, tags=["Inference"])
def get_forecast(
    station_id: int = Path(..., ge=0, description="Station identifier to forecast"),
):
    """
    Executes future river-level prediction for a station using recent observations.
    Compares the predicted level with CWC thresholds and returns explainable risk classification.
    """
    try:
        res = service.forecast_for_station(station_id=station_id)
        return ForecastResponse(**res)
    except DataValidationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal forecast error: {str(e)}")


@app.get("/risk/{station_id}", response_model=RiskAssessmentResponse, tags=["Decision Support"])
def get_current_risk(
    station_id: int = Path(..., ge=0),
):
    """Evaluates risk classification and advisory based on the latest observed water level."""
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
    except DataValidationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/thresholds/{station_id}", response_model=ThresholdResponse, tags=["Thresholds"])
def get_station_thresholds(
    station_id: int = Path(..., ge=0),
):
    """Retrieves CWC Warning Level, Danger Level, and HFL for a station with verification status."""
    meta = service.data_loader.get_station_metadata(station_id)
    if not meta:
        raise HTTPException(status_code=404, detail=f"Station ID {station_id} not found.")
    return ThresholdResponse(
        station_id=station_id,
        station_name=meta.get("Station", f"Station {station_id}").strip(),
        river=meta.get("River"),
        warning_level=meta.get("warning_level"),
        danger_level=meta.get("danger_level"),
        hfl=meta.get("hfl"),
        status=meta.get("threshold_status", "UNAVAILABLE"),
        source=meta.get("threshold_source", "UNAVAILABLE"),
    )


@app.get("/model/metrics", response_model=List[MetricItem], tags=["Evaluation"])
def get_model_metrics():
    """Retrieves empirical test evaluation metrics across baseline models and LSTM."""
    return service.get_metrics_summary()


@app.post("/forecast", response_model=ForecastResponse, tags=["Inference"])
def forecast_custom_readings(req: CustomForecastRequest):
    """
    Backwards-compatible endpoint: accepts an externally supplied array of recent readings
    and returns predicted future river level and risk assessment.
    """
    try:
        custom_records = [{"timestamp": r.timestamp, "water_level": r.water_level} for r in req.readings]
        custom_df = pd.DataFrame(custom_records)
        custom_df["timestamp"] = pd.to_datetime(custom_df["timestamp"])
        res = service.forecast_for_station(
            station_id=req.station_id,
            custom_df=custom_df,
            sequence_length=req.sequence_length,
        )
        return ForecastResponse(**res)
    except DataValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
