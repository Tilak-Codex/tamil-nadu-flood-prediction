"""
Feature engineering module for river water level time series.
Derives cyclical temporal, meteorological, and rolling autoregressive features.
"""

import numpy as np
import pandas as pd
from typing import Set

from src.config import MONSOON_MONTHS


def add_temporal_features(df: pd.DataFrame, ts_col: str = "timestamp") -> pd.DataFrame:
    """Adds cyclical hour and day-of-year features plus monsoon indicator."""
    df = df.copy()
    ts = pd.to_datetime(df[ts_col])
    
    hour = ts.dt.hour
    df["hour_sin"] = np.sin(2 * np.pi * hour / 24.0)
    df["hour_cos"] = np.cos(2 * np.pi * hour / 24.0)

    doy = ts.dt.dayofyear
    df["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    df["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)

    df["is_monsoon"] = ts.dt.month.isin(MONSOON_MONTHS).astype(int)
    return df


def add_hydrologic_features(
    df: pd.DataFrame,
    target_col: str = "water_level",
    segment_col: str = "segment_id",
    rolling_window: int = 24,
) -> pd.DataFrame:
    """
    Computes rate of change and rolling stats, bounded strictly within segment_id
    to prevent cross-gap contamination.
    """
    df = df.copy()

    if segment_col in df.columns:
        # Grouped by segment to respect gap boundaries
        df["rate_of_change"] = (
            df.groupby(segment_col)[target_col].diff().fillna(0.0)
        )
        df["rolling_mean_24h"] = (
            df.groupby(segment_col)[target_col]
            .transform(lambda x: x.rolling(rolling_window, min_periods=1).mean())
        )
        df["rolling_std_24h"] = (
            df.groupby(segment_col)[target_col]
            .transform(lambda x: x.rolling(rolling_window, min_periods=1).std().fillna(0.0))
        )
    else:
        df["rate_of_change"] = df[target_col].diff().fillna(0.0)
        df["rolling_mean_24h"] = df[target_col].rolling(rolling_window, min_periods=1).mean()
        df["rolling_std_24h"] = df[target_col].rolling(rolling_window, min_periods=1).std().fillna(0.0)

    return df


def ensure_meteorological_features(df: pd.DataFrame) -> pd.DataFrame:
    """Ensures rainfall, temperature, and pressure columns exist with sensible physical defaults."""
    df = df.copy()
    if "rainfall" not in df.columns:
        df["rainfall"] = 0.0
    else:
        df["rainfall"] = pd.to_numeric(df["rainfall"], errors="coerce").fillna(0.0)

    if "temperature" not in df.columns:
        if "timestamp" in df.columns:
            ts = pd.to_datetime(df["timestamp"])
            hours = ts.dt.hour.to_numpy()
            df["temperature"] = 28.0 + 4.0 * np.sin(2 * np.pi * (hours - 9) / 24.0)
        else:
            df["temperature"] = 28.0
    else:
        df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce").fillna(28.0)

    if "pressure" not in df.columns:
        df["pressure"] = 1010.0
    else:
        df["pressure"] = pd.to_numeric(df["pressure"], errors="coerce").fillna(1010.0)

    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Full feature engineering pipeline for historical or inference data."""
    df = ensure_meteorological_features(df)
    df = add_temporal_features(df)
    df = add_hydrologic_features(df)
    return df
