"""
Time-series sequence builder with strict chronological splitting
and zero data leakage.
"""

from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from src.config import (
    NUMERIC_FEATURES,
    TARGET_COL,
    LOOKBACK,
    FORECAST_HORIZON,
    TRAIN_RATIO,
    VAL_RATIO,
)


def chronological_split_station(
    df_station: pd.DataFrame,
    train_ratio: float = TRAIN_RATIO,
    val_ratio: float = VAL_RATIO,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Performs strict chronological splitting on a station's time series.
    Guarantees Train < Val < Test chronologically.
    """
    df_sorted = df_station.sort_values("timestamp").reset_index(drop=True)
    n = len(df_sorted)
    i_train = int(n * train_ratio)
    i_val = int(n * (train_ratio + val_ratio))

    train_df = df_sorted.iloc[:i_train].copy()
    val_df = df_sorted.iloc[i_train:i_val].copy()
    test_df = df_sorted.iloc[i_val:].copy()
    return train_df, val_df, test_df


def fit_and_scale_splits(
    train_parts: List[pd.DataFrame],
    val_parts: List[pd.DataFrame],
    test_parts: List[pd.DataFrame],
    feature_cols: List[str] = NUMERIC_FEATURES,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[int, MinMaxScaler]]:
    """
    CRITICAL: Fits MinMaxScaler EXCLUSIVELY on training data for each station.
    Applies the fitted scalers to validation and test data, eliminating data leakage.
    """
    scalers: Dict[int, MinMaxScaler] = {}
    scaled_train_list = []
    scaled_val_list = []
    scaled_test_list = []

    for tr, val, te in zip(train_parts, val_parts, test_parts):
        if tr.empty:
            continue
        sid = int(tr["station_id"].iloc[0])
        scaler = MinMaxScaler()
        
        # Fit ONLY on train split
        scaler.fit(tr[feature_cols])
        scalers[sid] = scaler

        tr_scaled = tr.copy()
        tr_scaled[feature_cols] = scaler.transform(tr[feature_cols])
        scaled_train_list.append(tr_scaled)

        if not val.empty:
            val_scaled = val.copy()
            val_scaled[feature_cols] = scaler.transform(val[feature_cols])
            scaled_val_list.append(val_scaled)

        if not te.empty:
            te_scaled = te.copy()
            te_scaled[feature_cols] = scaler.transform(te[feature_cols])
            scaled_test_list.append(te_scaled)

    train_scaled_df = pd.concat(scaled_train_list, ignore_index=True) if scaled_train_list else pd.DataFrame()
    val_scaled_df = pd.concat(scaled_val_list, ignore_index=True) if scaled_val_list else pd.DataFrame()
    test_scaled_df = pd.concat(scaled_test_list, ignore_index=True) if scaled_test_list else pd.DataFrame()

    return train_scaled_df, val_scaled_df, test_scaled_df, scalers


from numpy.lib.stride_tricks import sliding_window_view


def build_sequences_for_station(
    df_station: pd.DataFrame,
    sequence_length: int = LOOKBACK,
    horizon: int = FORECAST_HORIZON,
    feature_cols: List[str] = NUMERIC_FEATURES,
    target_col: str = TARGET_COL,
) -> Tuple[np.ndarray, np.ndarray, List[pd.Timestamp]]:
    """
    Constructs sliding window sequences for a station using vectorized NumPy strides.
    Respects segment_id boundaries: a sequence NEVER crosses a gap boundary.
    Returns:
        X: 3D array shape (num_sequences, sequence_length, n_features)
        y: 1D array of target values at t + sequence_length + horizon - 1
        timestamps: The timestamp corresponding to each target y
    """
    target_idx = feature_cols.index(target_col)
    segment_col = "segment_id" if "segment_id" in df_station.columns else None
    groups = df_station.groupby(segment_col, sort=False) if segment_col else [(None, df_station)]

    X_list, y_list, ts_list = [], [], []
    needed = sequence_length + horizon
    n_features = len(feature_cols)

    for _, seg in groups:
        n = len(seg)
        if n < needed:
            continue
        seg = seg.sort_values("timestamp")
        vals = seg[feature_cols].to_numpy(dtype=np.float32)
        ts_vals = seg["timestamp"].to_numpy()

        windows = sliding_window_view(vals, (sequence_length, n_features))[:, 0, :, :]
        targets = vals[sequence_length + horizon - 1 : n, target_idx]
        windows = windows[: len(targets)]
        target_ts = ts_vals[sequence_length + horizon - 1 : n]

        X_list.append(windows)
        y_list.append(targets)
        ts_list.extend(target_ts)

    if X_list:
        return np.concatenate(X_list, axis=0), np.concatenate(y_list, axis=0), ts_list
    else:
        return (
            np.empty((0, sequence_length, n_features), dtype=np.float32),
            np.empty((0,), dtype=np.float32),
            [],
        )


def prepare_dataset_sequences(
    df: pd.DataFrame,
    sequence_length: int = LOOKBACK,
    horizon: int = FORECAST_HORIZON,
    feature_cols: List[str] = NUMERIC_FEATURES,
    train_ratio: float = TRAIN_RATIO,
    val_ratio: float = VAL_RATIO,
) -> Tuple[
    Tuple[np.ndarray, np.ndarray, np.ndarray, List[pd.Timestamp]],
    Tuple[np.ndarray, np.ndarray, np.ndarray, List[pd.Timestamp]],
    Tuple[np.ndarray, np.ndarray, np.ndarray, List[pd.Timestamp]],
    Dict[int, MinMaxScaler],
]:
    """
    End-to-end leak-free sequence preparation across all stations.
    Returns:
        (X_train, y_train, sid_train, ts_train),
        (X_val, y_val, sid_val, ts_val),
        (X_test, y_test, sid_test, ts_test),
        scalers
    """
    train_parts, val_parts, test_parts = [], [], []

    for sid, st_df in df.groupby("station_id", sort=False):
        tr, val, te = chronological_split_station(st_df, train_ratio, val_ratio)
        train_parts.append(tr)
        val_parts.append(val)
        test_parts.append(te)

    tr_scaled, val_scaled, te_scaled, scalers = fit_and_scale_splits(
        train_parts, val_parts, test_parts, feature_cols
    )

    def extract_xy(split_df):
        Xs, ys, sids, tss = [], [], [], []
        for sid, g in split_df.groupby("station_id", sort=False):
            Xg, yg, tsg = build_sequences_for_station(
                g, sequence_length, horizon, feature_cols, TARGET_COL
            )
            if len(Xg) > 0:
                Xs.append(Xg)
                ys.append(yg)
                sids.append(np.full(len(Xg), sid, dtype=np.int32))
                tss.extend(tsg)
        if Xs:
            return (
                np.concatenate(Xs, axis=0),
                np.concatenate(ys, axis=0),
                np.concatenate(sids, axis=0),
                tss,
            )
        else:
            return (
                np.empty((0, sequence_length, len(feature_cols)), dtype=np.float32),
                np.empty((0,), dtype=np.float32),
                np.empty((0,), dtype=np.int32),
                [],
            )

    train_data = extract_xy(tr_scaled)
    val_data = extract_xy(val_scaled)
    test_data = extract_xy(te_scaled)

    return train_data, val_data, test_data, scalers
