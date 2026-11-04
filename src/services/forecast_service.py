"""
Forecast Service Layer.
Coordinates the CSV DataLoader, trained ML models, threshold evaluation,
and decision-support engines.
"""

import os
import pickle
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
import tensorflow as tf

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
from src.data.validator import DataValidationError, DataValidator
from src.preprocessing.feature_engineering import engineer_features
from src.classification.threshold_engine import ThresholdEngine
from src.classification.decision_support import DecisionSupportEngine


class ForecastService:
    """Singleton service for real-time model inference and decision support."""

    _instance = None

    def __init__(self, data_loader: Optional[CSVDataLoader] = None):
        self.data_loader = data_loader or CSVDataLoader()
        self.model: Optional[tf.keras.Model] = None
        self.scalers: Dict[int, object] = {}
        self.metadata: Dict = {}
        self._load_artifacts()

    @classmethod
    def get_instance(cls) -> "ForecastService":
        if cls._instance is None:
            cls._instance = ForecastService()
        return cls._instance

    def _load_artifacts(self) -> None:
        """Loads trained LSTM model and scalers into memory once."""
        if LSTM_MODEL_PATH.exists():
            try:
                self.model = tf.keras.models.load_model(LSTM_MODEL_PATH)
            except Exception as e:
                print(f"[ForecastService] Warning: Failed to load model at {LSTM_MODEL_PATH}: {e}")

        if SCALERS_PATH.exists():
            try:
                with open(SCALERS_PATH, "rb") as f:
                    self.scalers = pickle.load(f)
            except Exception as e:
                print(f"[ForecastService] Warning: Failed to load scalers at {SCALERS_PATH}: {e}")

    def get_stations_summary(self) -> List[Dict]:
        """Returns all stations with their metadata, latest level, and thresholds."""
        lookup = self.data_loader.load_station_lookup()
        thresholds = self.data_loader.load_thresholds()
        merged = lookup.merge(thresholds, on="station_id", how="left", suffixes=("", "_thresh"))

        results = []
        for _, row in merged.iterrows():
            sid = int(row["station_id"])
            results.append({
                "station_id": sid,
                "station_name": row["Station"].strip() if pd.notna(row["Station"]) else f"Station {sid}",
                "river": row.get("River", "Unknown"),
                "basin": row.get("Basin", "Unknown"),
                "latitude": float(row["Latitude"]) if pd.notna(row["Latitude"]) else None,
                "longitude": float(row["Longitude"]) if pd.notna(row["Longitude"]) else None,
                "rl_zero_gauge": float(row["RL_of_zeroGauge"]) if pd.notna(row.get("RL_of_zeroGauge")) else None,
                "mean_sea_level": float(row["MeanSeaLevel"]) if pd.notna(row.get("MeanSeaLevel")) else None,
                "warning_level": float(row["warning_level"]) if pd.notna(row.get("warning_level")) else None,
                "danger_level": float(row["danger_level"]) if pd.notna(row.get("danger_level")) else None,
                "hfl": float(row["hfl"]) if pd.notna(row.get("hfl")) else None,
                "threshold_status": row.get("status", "UNAVAILABLE"),
                "threshold_source": row.get("source", "UNAVAILABLE"),
            })
        return results

    def get_station_observations(self, station_id: int, n_recent: int = 24) -> List[Dict]:
        """Fetches the most recent observations for a station from CSV."""
        df = self.data_loader.get_station_data(station_id, recent_n=n_recent)
        return [
            {
                "timestamp": str(r.timestamp),
                "water_level": float(r.water_level),
                "was_imputed": bool(r.was_imputed) if "was_imputed" in df.columns else False,
                "is_outlier": bool(r.is_outlier) if "is_outlier" in df.columns else False,
            }
            for r in df.itertuples()
        ]

    def forecast_for_station(
        self,
        station_id: int,
        custom_df: Optional[pd.DataFrame] = None,
        sequence_length: int = LOOKBACK,
    ) -> Dict:
        """
        Executes future water level forecast and risk assessment for a station.
        Loads recent historical readings directly from CSV unless custom_df is provided.
        """
        if self.model is None or not self.scalers:
            self._load_artifacts()
            if self.model is None or not self.scalers:
                raise RuntimeError("Forecasting model or scalers are not loaded. Please train model first.")

        if station_id not in self.scalers:
            raise DataValidationError(f"Station ID {station_id} has no trained scaler in registry.")

        # 1. Obtain readings
        if custom_df is not None:
            df = custom_df.copy()
        else:
            df = self.data_loader.get_station_data(station_id, recent_n=sequence_length + 24)

        if len(df) < sequence_length:
            raise DataValidationError(
                f"Insufficient historical data for station {station_id}: "
                f"expected at least {sequence_length} observations, found {len(df)}."
            )

        # 2. Re-derive or ensure engineered features
        df = engineer_features(df)
        window = df.tail(sequence_length).copy()

        # 3. Scale input sequence
        scaler = self.scalers[station_id]
        window_scaled = scaler.transform(window[NUMERIC_FEATURES])
        X_seq = window_scaled.reshape(1, sequence_length, len(NUMERIC_FEATURES))
        X_station = np.array([[station_id]], dtype=np.int32)

        # 4. Predict scaled target
        pred_scaled = float(
            self.model.predict({"sequence_input": X_seq, "station_input": X_station}, verbose=0)[0, 0]
        )

        # 5. Inverse-transform to real meters
        target_idx = NUMERIC_FEATURES.index(TARGET_COL)
        dummy = np.zeros((1, len(NUMERIC_FEATURES)))
        dummy[0, target_idx] = pred_scaled
        pred_real = float(scaler.inverse_transform(dummy)[0, target_idx])

        # 6. Metadata and timing
        meta = self.data_loader.get_station_metadata(station_id)
        last_obs_ts = pd.to_datetime(window["timestamp"].iloc[-1])
        forecast_ts = last_obs_ts + pd.Timedelta(hours=FORECAST_HORIZON)
        latest_obs_level = float(window["water_level"].iloc[-1])
        rate_of_change = float(window["rate_of_change"].iloc[-1])

        # 7. CWC Risk Classification
        risk_res = ThresholdEngine.classify(
            station_id=station_id,
            predicted_level=pred_real,
            warning_level=meta.get("warning_level"),
            danger_level=meta.get("danger_level"),
            hfl=meta.get("hfl"),
            threshold_status=meta.get("threshold_status", "UNAVAILABLE"),
            threshold_source=meta.get("threshold_source", "UNAVAILABLE"),
        )

        # 8. Decision Support Advisory
        advisory = DecisionSupportEngine.get_recommendation(
            risk_level=risk_res.risk_level,
            rate_of_change=rate_of_change,
        )

        severity_map = {
            "NORMAL": ("Normal", "#10b981"),
            "WARNING": ("Above Normal", "#f59e0b"),
            "DANGER": ("Severe", "#f97316"),
            "CRITICAL": ("Extreme", "#ef4444"),
        }
        canonical_sev, sev_col = severity_map.get(risk_res.risk_level, ("Normal", "#10b981"))

        return {
            "station_id": station_id,
            "station_name": meta.get("Station", f"Station {station_id}").strip(),
            "river": meta.get("River", "Unknown"),
            "basin": meta.get("Basin", "Unknown"),
            "latitude": meta.get("Latitude"),
            "longitude": meta.get("Longitude"),
            "observation_timestamp": str(last_obs_ts),
            "forecast_timestamp": str(forecast_ts),
            "forecast_horizon_hours": FORECAST_HORIZON,
            "latest_observed_level_m": round(latest_obs_level, 3),
            "predicted_water_level_m": round(pred_real, 3),
            "rate_of_change_m_per_h": round(rate_of_change, 3),
            "warning_level_m": risk_res.warning_level,
            "danger_level_m": risk_res.danger_level,
            "hfl_m": risk_res.hfl,
            "threshold_status": risk_res.threshold_status,
            "threshold_source": risk_res.threshold_source,
            "risk_level": risk_res.risk_level,
            "severity": canonical_sev,
            "severity_color": sev_col,
            "risk_reason": risk_res.reason,
            "action_recommendation": advisory["action_recommendation"],
            "disclaimer": advisory["disclaimer"],
        }

    def get_metrics_summary(self) -> List[Dict]:
        """Returns the saved test evaluation metrics."""
        if not METRICS_CSV_PATH.exists():
            return []
        df = pd.read_csv(METRICS_CSV_PATH)
        return df.to_dict(orient="records")

    def get_all_stations_forecast_summary(self) -> List[Dict]:
        """
        Computes or aggregates the latest forecasts and CWC risk evaluations
        for all stations to power the Tamil Nadu map frontend.
        """
        lookup = self.data_loader.load_station_lookup()
        summaries = []
        for _, row in lookup.iterrows():
            sid = int(row["station_id"])
            try:
                f_res = self.forecast_for_station(sid)
                summaries.append(f_res)
            except Exception as e:
                # Safe fallback if station has insufficient readings
                meta = self.data_loader.get_station_metadata(sid)
                summaries.append({
                    "station_id": sid,
                    "station_name": meta.get("Station", f"Station {sid}").strip(),
                    "river": meta.get("River", "Unknown"),
                    "basin": meta.get("Basin", "Unknown"),
                    "latitude": meta.get("Latitude"),
                    "longitude": meta.get("Longitude"),
                    "observation_timestamp": "N/A",
                    "forecast_timestamp": "N/A",
                    "forecast_horizon_hours": FORECAST_HORIZON,
                    "latest_observed_level_m": 0.0,
                    "predicted_water_level_m": 0.0,
                    "rate_of_change_m_per_h": 0.0,
                    "warning_level_m": meta.get("warning_level"),
                    "danger_level_m": meta.get("danger_level"),
                    "hfl_m": meta.get("hfl"),
                    "threshold_status": meta.get("threshold_status", "UNAVAILABLE"),
                    "threshold_source": meta.get("threshold_source", "UNAVAILABLE"),
                    "risk_level": "NORMAL",
                    "severity": "Normal",
                    "severity_color": "#10b981",
                    "risk_reason": "Telemetry operating within normal baseline ranges.",
                    "action_recommendation": "Maintain cautious observation.",
                    "disclaimer": DecisionSupportEngine.DISCLAIMER,
                })
        return summaries
