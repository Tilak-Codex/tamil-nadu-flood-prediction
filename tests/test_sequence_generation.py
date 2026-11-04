"""
Unit tests for chronological sequence builder and leak-free scaling.
"""

import pytest
import numpy as np
import pandas as pd
from src.preprocessing.sequence_builder import (
    chronological_split_station,
    fit_and_scale_splits,
    build_sequences_for_station,
)
from src.config import NUMERIC_FEATURES, TARGET_COL


def test_chronological_splitting_order():
    # Synthetic date series to verify order
    dates = pd.date_range("2021-01-01", periods=100, freq="1h")
    df = pd.DataFrame({
        "station_id": [0] * 100,
        "timestamp": dates,
        "water_level": np.arange(100, dtype=float),
    })
    
    train_df, val_df, test_df = chronological_split_station(df, train_ratio=0.7, val_ratio=0.15)
    
    assert len(train_df) == 70
    assert len(val_df) == 15
    assert len(test_df) == 15
    assert train_df["timestamp"].max() < val_df["timestamp"].min()
    assert val_df["timestamp"].max() < test_df["timestamp"].min()


def test_leak_free_scaler_fitting():
    # Train range [0, 50], Test range [51, 100]
    dates = pd.date_range("2021-01-01", periods=100, freq="1h")
    df = pd.DataFrame({
        "station_id": [0] * 100,
        "timestamp": dates,
        "water_level": np.arange(100, dtype=float),
    })
    # Add dummy numeric features
    for col in NUMERIC_FEATURES[1:]:
        df[col] = 0.0

    tr, val, te = chronological_split_station(df, 0.7, 0.15)
    tr_scaled, val_scaled, te_scaled, scalers = fit_and_scale_splits([tr], [val], [te], NUMERIC_FEATURES)

    scaler = scalers[0]
    # Scaler min and max should strictly match train min (0.0) and train max (69.0)
    wl_idx = NUMERIC_FEATURES.index("water_level")
    assert scaler.data_min_[wl_idx] == 0.0
    assert scaler.data_max_[wl_idx] == 69.0
    # Test values (70-99) will exceed 1.0 in scaled space, proving NO test data was leaked during fit!
    assert te_scaled["water_level"].max() > 1.0


def test_sequence_window_and_target_alignment():
    dates = pd.date_range("2021-01-01", periods=50, freq="1h")
    df = pd.DataFrame({
        "station_id": [0] * 50,
        "timestamp": dates,
        "segment_id": [0] * 50,
        "water_level": np.arange(50, dtype=float),
    })
    for col in NUMERIC_FEATURES[1:]:
        df[col] = 1.0

    lookback = 24
    horizon = 1
    X, y, ts = build_sequences_for_station(df, lookback, horizon, NUMERIC_FEATURES, "water_level")

    assert len(X) == 50 - (lookback + horizon) + 1
    assert X[0].shape == (lookback, len(NUMERIC_FEATURES))
    # Target for sequence 0 must be value at index lookback + horizon - 1 = 24
    assert y[0] == 24.0
    # Timestamp for sequence 0 must be dates[24]
    assert ts[0] == dates[24]
