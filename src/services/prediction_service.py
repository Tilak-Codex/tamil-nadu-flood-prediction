"""
Prediction Service for Deep Learning (LSTM) River Level Forecasting.
Coordinates data validation, feature scaling, model inference,
severity evaluation, and persistence into the database.
"""

import pickle
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd
import tensorflow as tf
from sqlalchemy.orm import Session

from src.config import (
    LSTM_MODEL_PATH,
    SCALERS_PATH,
    METADATA_PATH,
    METRICS_CSV_PATH,
    LOOKBACK,
    FORECAST_HORIZON,
    NUMERIC_FEATURES,
    TARGET_COL,
)
from src.data.loader import CSVDataLoader
from src.data.validator import DataValidationError
from src.preprocessing.feature_engineering import engineer_features
from src.services.severity_service import FloodSeverityService
from src.repositories.station_repository import StationRepository
from src.repositories.observation_repository import ObservationRepository
from src.repositories.prediction_repository import PredictionRepository

logger = logging.getLogger(__name__)


class PredictionService:
    _instance = None

    def __init__(self, data_loader: Optional[CSVDataLoader] = None):
        self.data_loader = data_loader or CSVDataLoader()
        self.model: Optional[tf.keras.Model] = None
        self.scalers: Dict[int, object] = {}
        self.metadata: Dict = {}
        self._load_artifacts()

    @classmethod
    def get_instance(cls) -> "PredictionService":
        if cls._instance is None:
            cls._instance = PredictionService()
        return cls._instance

    def _load_artifacts(self) -> None:
        if LSTM_MODEL_PATH.exists():
            try:
                self.model = tf.keras.models.load_model(LSTM_MODEL_PATH)
            except Exception as e:
                logger.error(f"Failed to load LSTM model at {LSTM_MODEL_PATH}: {e}")

        if SCALERS_PATH.exists():
            try:
                with open(SCALERS_PATH, "rb") as f:
                    self.scalers = pickle.load(f)
            except Exception as e:
                logger.error(f"Failed to load scalers at {SCALERS_PATH}: {e}")

    def run_prediction(
        self,
        station_id: int,
        db: Optional[Session] = None,
        custom_df: Optional[pd.DataFrame] = None,
        sequence_length: int = LOOKBACK,
    ) -> Dict[str, Any]:
        """
        Executes future river-level prediction for a station using exactly sequence_length (24) observations.
        Validates input shape, scalers, and lookback window.
        Stores resulting prediction in database when db session is supplied.
        """
        if self.model is None or not self.scalers:
            self._load_artifacts()
            if self.model is None or not self.scalers:
                raise RuntimeError("Forecasting model or scalers are not loaded. Artifacts missing.")

        if station_id not in self.scalers:
            raise DataValidationError(f"Station ID {station_id} has no trained scaler in registry.")

        # 1. Fetch sequence readings
        if custom_df is not None:
            df = custom_df.copy()
        elif db is not None:
            # Check if database has sufficient observations
            obs_repo = ObservationRepository(db)
            db_obs = obs_repo.get_history(station_id, limit=sequence_length + 24)
            valid_wl_obs = [o for o in db_obs if o.water_level is not None]
            if len(valid_wl_obs) >= sequence_length:
                df = pd.DataFrame([
                    {"timestamp": o.timestamp, "water_level": o.water_level}
                    for o in valid_wl_obs
                ])
            else:
                # Fallback to verified CSV telemetry loader
                df = self.data_loader.get_station_data(station_id, recent_n=sequence_length + 24)
        else:
            df = self.data_loader.get_station_data(station_id, recent_n=sequence_length + 24)

        if len(df) < sequence_length:
            raise DataValidationError(
                f"Insufficient historical observations for station {station_id}: "
                f"expected at least {sequence_length} readings, found {len(df)}."
            )

        # 2. Engineer features (cyclical time, rate of change, rolling stats)
        df = engineer_features(df)
        window = df.tail(sequence_length).copy()

        # 3. Scale input features using station-specific fitted scaler
        scaler = self.scalers[station_id]
        window_scaled = scaler.transform(window[NUMERIC_FEATURES])
        X_seq = window_scaled.reshape(1, sequence_length, len(NUMERIC_FEATURES))
        X_station = np.array([[station_id]], dtype=np.int32)

        # 4. Neural Network Inference
        pred_scaled = float(
            self.model.predict({"sequence_input": X_seq, "station_input": X_station}, verbose=0)[0, 0]
        )

        # 5. Inverse-transform to meters
        target_idx = NUMERIC_FEATURES.index(TARGET_COL)
        dummy = np.zeros((1, len(NUMERIC_FEATURES)))
        dummy[0, target_idx] = pred_scaled
        pred_real = float(scaler.inverse_transform(dummy)[0, target_idx])

        # 6. Metadata and Timings
        meta = self.data_loader.get_station_metadata(station_id)
        last_obs_ts = pd.to_datetime(window["timestamp"].iloc[-1])
        if last_obs_ts.tzinfo is None:
            last_obs_ts = last_obs_ts.replace(tzinfo=timezone.utc)
        forecast_ts = last_obs_ts + timedelta(hours=FORECAST_HORIZON)
        latest_obs_level = float(window["water_level"].iloc[-1])
        rate_of_change = float(window["rate_of_change"].iloc[-1])

        # 7. Severity classification
        sev_res = FloodSeverityService.classify(
            station_id=station_id,
            predicted_level=pred_real,
            warning_level=meta.get("warning_level"),
            danger_level=meta.get("danger_level"),
            hfl=meta.get("hfl"),
            threshold_status=meta.get("threshold_status", "UNAVAILABLE"),
            threshold_source=meta.get("threshold_source", "UNAVAILABLE"),
            rate_of_change=rate_of_change,
        )

        # 8. Store in database if db session provided
        now_utc = datetime.now(timezone.utc)
        if db is not None:
            pred_repo = PredictionRepository(db)
            pred_repo.save(
                station_id=station_id,
                target_timestamp=forecast_ts,
                predicted_water_level=round(pred_real, 3),
                latest_observed_level=round(latest_obs_level, 3),
                rate_of_change=round(rate_of_change, 3),
                severity=sev_res.severity,
                severity_reason=sev_res.reason,
                action_recommendation=sev_res.action_recommendation,
                forecast_horizon_hours=FORECAST_HORIZON,
                model_version="Functional_LSTM_With_Station_Embedding",
                input_quality_status="VALID",
                generation_timestamp=now_utc,
            )

        return {
            "station_id": station_id,
            "station_name": meta.get("Station", f"Station {station_id}").strip(),
            "river": meta.get("River", "Unknown"),
            "basin": meta.get("Basin", "Unknown"),
            "latitude": meta.get("Latitude"),
            "longitude": meta.get("Longitude"),
            "generation_timestamp": now_utc.isoformat(),
            "observation_timestamp": last_obs_ts.isoformat(),
            "target_timestamp": forecast_ts.isoformat(),
            "forecast_horizon_hours": FORECAST_HORIZON,
            "latest_observed_level_m": round(latest_obs_level, 3),
            "predicted_water_level_m": round(pred_real, 3),
            "rate_of_change_m_per_h": round(rate_of_change, 3),
            "warning_level_m": sev_res.warning_level,
            "danger_level_m": sev_res.danger_level,
            "hfl_m": sev_res.hfl,
            "threshold_status": sev_res.threshold_status,
            "threshold_source": sev_res.threshold_source,
            "threshold_basis": sev_res.basis,
            "severity": sev_res.severity,
            "severity_color": sev_res.severity_color,
            "severity_reason": sev_res.reason,
            "action_recommendation": sev_res.action_recommendation,
            "disclaimer": sev_res.disclaimer,
            "model_version": "Functional_LSTM_With_Station_Embedding",
            "model_status": "OPERATIONAL",
        }
