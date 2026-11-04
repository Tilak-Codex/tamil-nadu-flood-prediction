"""
SQLAlchemy ORM models for Stations, Observations, Weather, Thresholds, Predictions, and Alerts.
Supports PostgreSQL (production) and SQLite (development).
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    Text,
    Boolean,
)
from sqlalchemy.orm import relationship

from src.database.connection import Base


class Station(Base):
    __tablename__ = "stations"

    station_id = Column(Integer, primary_key=True, index=True)
    station_name = Column(String(120), nullable=False, index=True)
    river = Column(String(80), nullable=False)
    basin = Column(String(80), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    rl_zero_gauge = Column(Float, nullable=True)
    mean_sea_level = Column(Float, nullable=True)
    warning_level = Column(Float, nullable=True)
    danger_level = Column(Float, nullable=True)
    hfl = Column(Float, nullable=True)
    threshold_status = Column(String(50), default="UNAVAILABLE")
    threshold_source = Column(String(100), default="UNAVAILABLE")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    observations = relationship("Observation", back_populates="station", cascade="all, delete-orphan")
    weather_observations = relationship("WeatherObservation", back_populates="station", cascade="all, delete-orphan")
    thresholds = relationship("FloodThreshold", back_populates="station", uselist=False, cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="station", cascade="all, delete-orphan")
    alerts = relationship("FloodAlert", back_populates="station", cascade="all, delete-orphan")


class Observation(Base):
    __tablename__ = "observations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    station_id = Column(Integer, ForeignKey("stations.station_id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    water_level = Column(Float, nullable=True)  # In meters
    rainfall = Column(Float, nullable=True)     # In mm
    temperature = Column(Float, nullable=True)  # In °C
    pressure = Column(Float, nullable=True)     # In hPa
    data_source = Column(String(50), nullable=False)  # CWC_TELEMETRY, NWDP, TN_WRD, OPEN_METEO, etc.
    data_type = Column(String(30), nullable=False, default="OBSERVED")  # OBSERVED, FORECASTED, HISTORICAL, SAMPLE
    quality_status = Column(String(30), nullable=False, default="VALID")  # VALID, STALE, IMPUTED, UNAVAILABLE
    was_imputed = Column(Boolean, default=False)
    is_outlier = Column(Boolean, default=False)
    fetched_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    station = relationship("Station", back_populates="observations")

    __table_args__ = (
        UniqueConstraint("station_id", "timestamp", "data_type", name="uq_station_time_type"),
        Index("ix_station_timestamp", "station_id", "timestamp"),
    )


class WeatherObservation(Base):
    __tablename__ = "weather_observations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    station_id = Column(Integer, ForeignKey("stations.station_id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    rainfall = Column(Float, nullable=False, default=0.0)      # Precipitation in mm
    temperature = Column(Float, nullable=False, default=28.0)  # In °C
    pressure = Column(Float, nullable=False, default=1010.0)   # In hPa
    relative_humidity = Column(Float, nullable=True)           # In %
    data_source = Column(String(50), nullable=False, default="OPEN_METEO")  # OPEN_METEO, IMD_AWS, HISTORICAL_ENRICHED
    data_type = Column(String(30), nullable=False, default="OBSERVED")      # OBSERVED, FORECASTED, HISTORICAL, SAMPLE
    quality_status = Column(String(30), nullable=False, default="VALID")    # VALID, IMPUTED, UNAVAILABLE
    fetched_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    station = relationship("Station", back_populates="weather_observations")

    __table_args__ = (
        UniqueConstraint("station_id", "timestamp", "data_source", name="uq_station_weather_time"),
        Index("ix_weather_station_time", "station_id", "timestamp"),
    )


class FloodThreshold(Base):
    __tablename__ = "flood_thresholds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    station_id = Column(Integer, ForeignKey("stations.station_id"), unique=True, nullable=False, index=True)
    warning_level = Column(Float, nullable=True)
    danger_level = Column(Float, nullable=True)
    hfl = Column(Float, nullable=True)
    status = Column(String(50), nullable=False, default="UNAVAILABLE")  # VERIFIED_CWC, DUMMY_PLACEHOLDER, UNAVAILABLE
    source = Column(String(100), nullable=False, default="UNAVAILABLE")
    notes = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    station = relationship("Station", back_populates="thresholds")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    station_id = Column(Integer, ForeignKey("stations.station_id"), nullable=False, index=True)
    generation_timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    target_timestamp = Column(DateTime, nullable=False, index=True)
    forecast_horizon_hours = Column(Integer, default=1)
    predicted_water_level = Column(Float, nullable=False)
    latest_observed_level = Column(Float, nullable=False)
    rate_of_change = Column(Float, nullable=False, default=0.0)
    severity = Column(String(40), nullable=False)  # Normal, Above Normal, Severe, Extreme, Threshold Unavailable
    severity_reason = Column(Text, nullable=True)
    action_recommendation = Column(Text, nullable=True)
    model_version = Column(String(50), default="LSTM_v2_Embedding")
    input_quality_status = Column(String(30), default="VALID")

    station = relationship("Station", back_populates="predictions")

    __table_args__ = (
        Index("ix_pred_station_target", "station_id", "target_timestamp"),
    )


class FloodAlert(Base):
    __tablename__ = "flood_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    station_id = Column(Integer, ForeignKey("stations.station_id"), nullable=False, index=True)
    severity = Column(String(40), nullable=False)  # Normal, Above Normal, Severe, Extreme
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    current_water_level = Column(Float, nullable=False)
    threshold_level = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    station = relationship("Station", back_populates="alerts")


class DataSourceStatus(Base):
    __tablename__ = "data_source_status"

    source_name = Column(String(80), primary_key=True)
    status = Column(String(40), nullable=False)  # CONNECTED, AUTHENTICATION_REQUIRED, OFFLINE_TIMEOUT, UNAVAILABLE
    last_successful_fetch = Column(DateTime, nullable=True)
    latest_observation_time = Column(DateTime, nullable=True)
    error_details = Column(Text, nullable=True)
    update_frequency = Column(String(50), default="Hourly")
    api_endpoint = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
