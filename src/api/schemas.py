"""
Pydantic schemas for the FastAPI Flood Forecasting & Decision Support API.
Maintains backwards compatibility while supporting extended canonical fields.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    scalers_count: int
    data_source: str = "SQLAlchemy / PostgreSQL / SQLite"
    database_connected: bool = True
    background_scheduler_active: bool = False


class StationSummary(BaseModel):
    station_id: int
    station_name: str
    river: Optional[str] = None
    basin: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    rl_zero_gauge: Optional[float] = None
    mean_sea_level: Optional[float] = None
    warning_level: Optional[float] = None
    danger_level: Optional[float] = None
    hfl: Optional[float] = None
    threshold_status: str
    threshold_source: str


class ObservationItem(BaseModel):
    timestamp: str
    water_level: Optional[float] = None
    rainfall: Optional[float] = None
    temperature: Optional[float] = None
    pressure: Optional[float] = None
    data_source: Optional[str] = "OPEN_METEO"
    data_type: Optional[str] = "OBSERVED"
    quality_status: Optional[str] = "VALID"
    was_imputed: bool = False
    is_outlier: bool = False


class StationObservationsResponse(BaseModel):
    station_id: int
    count: int
    observations: List[ObservationItem]


class ForecastResponse(BaseModel):
    station_id: int
    station_name: str
    river: Optional[str] = None
    basin: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    observation_timestamp: str
    forecast_timestamp: str
    forecast_horizon_hours: int = 1
    latest_observed_level_m: float
    predicted_water_level_m: float
    rate_of_change_m_per_h: float
    warning_level_m: Optional[float] = None
    danger_level_m: Optional[float] = None
    hfl_m: Optional[float] = None
    threshold_status: str
    threshold_source: str
    threshold_basis: Optional[str] = None
    risk_level: Optional[str] = None
    severity: Optional[str] = None
    severity_color: Optional[str] = None
    risk_reason: Optional[str] = None
    severity_reason: Optional[str] = None
    action_recommendation: str
    disclaimer: str
    model_version: Optional[str] = "Functional_LSTM_With_Station_Embedding"
    model_status: Optional[str] = "OPERATIONAL"


class RiskAssessmentResponse(BaseModel):
    station_id: int
    station_name: str
    water_level_m: float
    warning_level_m: Optional[float] = None
    danger_level_m: Optional[float] = None
    hfl_m: Optional[float] = None
    threshold_status: str
    threshold_source: str
    risk_level: str
    risk_reason: str
    action_recommendation: str
    disclaimer: str


class ThresholdResponse(BaseModel):
    station_id: int
    station_name: str
    river: Optional[str] = None
    warning_level: Optional[float] = None
    danger_level: Optional[float] = None
    hfl: Optional[float] = None
    status: str
    source: str


class MetricItem(BaseModel):
    station_id: Optional[int] = None
    station: Optional[str] = None
    model: str
    mae: Optional[float] = None
    rmse: Optional[float] = None
    r2: Optional[float] = None
    nse: Optional[float] = None
    samples: Optional[int] = None


class ReadingPayloadItem(BaseModel):
    timestamp: str
    water_level: float


class CustomForecastRequest(BaseModel):
    station_id: int
    sequence_length: int = 24
    readings: List[ReadingPayloadItem] = Field(..., min_length=1)


class DataSourceStatusResponse(BaseModel):
    source_name: str
    status: str
    last_successful_fetch: Optional[str] = None
    latest_observation_time: Optional[str] = None
    error_details: Optional[str] = None
    update_frequency: str
    api_endpoint: Optional[str] = None
    notes: Optional[str] = None


class DataRefreshResponse(BaseModel):
    status: str
    refreshed_at: str
    stations_processed: int
    observations_added_or_updated: int
    errors: List[str]
    source_statuses: Dict[str, str]


class RunPredictionRequest(BaseModel):
    station_id: int
    sequence_length: int = 24


class WeatherObservationItem(BaseModel):
    timestamp: str
    rainfall: float
    temperature: float
    pressure: float
    relative_humidity: Optional[float] = None
    data_source: str = "OPEN_METEO"
    data_type: str = "OBSERVED"
    quality_status: str = "VALID"


class AlertItem(BaseModel):
    id: int
    station_id: int
    station_name: Optional[str] = None
    river: Optional[str] = None
    severity: str
    title: str
    message: str
    current_water_level: float
    threshold_level: Optional[float] = None
    is_active: bool
    is_acknowledged: bool
    acknowledged_at: Optional[str] = None
    acknowledged_by: Optional[str] = None
    created_at: str


class AcknowledgeAlertRequest(BaseModel):
    acknowledged_by: str = "Duty Officer"


class DashboardStatsResponse(BaseModel):
    total_stations: int
    monitored_basins: int
    active_alerts: int
    critical_danger_count: int
    severe_warning_count: int
    normal_count: int
    threshold_unavailable_count: int
    latest_system_update: str
    model_operational: bool
    overall_r2: float
    overall_rmse: float
    data_sources_connected: int


class RiskSummaryResponse(BaseModel):
    category_counts: Dict[str, int]
    basin_distribution: Dict[str, Dict[str, int]]
    disclaimer: str
