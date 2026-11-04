"""
Baseline Models Training & Evaluation Script.
Evaluates Persistence (Naive), Moving Average, and Ridge Regression baselines
under strict chronological splitting with zero data leakage.
"""

import json
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import numpy as np
import pandas as pd

from src.config import (
    BASELINES_DIR,
    BASELINES_RESULTS_PATH,
    NUMERIC_FEATURES,
    TARGET_COL,
    LOOKBACK,
    FORECAST_HORIZON,
)
from src.data.loader import CSVDataLoader
from src.preprocessing.sequence_builder import prepare_dataset_sequences
from src.models.baselines import (
    NaivePersistenceModel,
    MovingAverageModel,
    RidgeAutoregressiveModel,
)
from src.evaluation.metrics import evaluate_forecasts


def main():
    print("=" * 80)
    print("TRAINING & EVALUATING BASELINE FORECASTING MODELS")
    print("=" * 80)

    BASELINES_DIR.mkdir(parents=True, exist_ok=True)
    loader = CSVDataLoader()
    df = loader.load_cleaned_data()
    lookup = loader.load_station_lookup()

    print("[1] Building leak-free train/val/test splits and sequences...")
    train_data, val_data, test_data, scalers = prepare_dataset_sequences(
        df,
        sequence_length=LOOKBACK,
        horizon=FORECAST_HORIZON,
        feature_cols=NUMERIC_FEATURES,
    )

    X_train, y_train, sid_train, ts_train = train_data
    X_val, y_val, sid_val, ts_val = val_data
    X_test, y_test, sid_test, ts_test = test_data

    print(f"    Train sequences: {len(X_train):,}")
    print(f"    Val sequences:   {len(X_val):,}")
    print(f"    Test sequences:  {len(X_test):,}")

    target_idx = NUMERIC_FEATURES.index(TARGET_COL)

    # Initialize baseline models
    baselines = {
        "Persistence_Naive": NaivePersistenceModel(target_idx=target_idx),
        "Moving_Average_24h": MovingAverageModel(target_idx=target_idx, window=24),
        "Ridge_Regression": RidgeAutoregressiveModel(alpha=1.0),
    }

    results = {}

    for name, model in baselines.items():
        print(f"\n[2] Training and evaluating {name}...")
        if name == "Ridge_Regression":
            # Train Ridge on a representative sample if train set is very large (e.g. 100k samples)
            sample_size = min(len(X_train), 100000)
            idx = np.random.RandomState(42).choice(len(X_train), sample_size, replace=False)
            model.fit(X_train[idx], y_train[idx])
        else:
            model.fit(X_train, y_train)

        # Generate test predictions in scaled space
        preds_scaled = model.predict(X_test)

        # Inverse transform per station to real meters
        y_test_real = np.zeros_like(y_test)
        preds_real = np.zeros_like(preds_scaled)

        station_metrics = {}
        for sid in np.unique(sid_test):
            mask = sid_test == sid
            if not np.any(mask):
                continue
            scaler = scalers[int(sid)]

            # Dummy matrices for inverse transform
            dummy_true = np.zeros((np.sum(mask), len(NUMERIC_FEATURES)))
            dummy_pred = np.zeros((np.sum(mask), len(NUMERIC_FEATURES)))
            dummy_true[:, target_idx] = y_test[mask]
            dummy_pred[:, target_idx] = preds_scaled[mask]

            st_true_real = scaler.inverse_transform(dummy_true)[:, target_idx]
            st_pred_real = scaler.inverse_transform(dummy_pred)[:, target_idx]

            y_test_real[mask] = st_true_real
            preds_real[mask] = st_pred_real

            st_res = evaluate_forecasts(st_true_real, st_pred_real)
            st_name = lookup.loc[lookup["station_id"] == sid, "Station"].values
            st_name_str = st_name[0].strip() if len(st_name) else f"Station_{sid}"
            station_metrics[int(sid)] = {
                "station_name": st_name_str,
                **st_res,
            }

        overall_metrics = evaluate_forecasts(y_test_real, preds_real)
        print(f"    Overall {name} -> MAE: {overall_metrics['mae']} m, RMSE: {overall_metrics['rmse']} m, R2: {overall_metrics['r2']}, NSE: {overall_metrics['nse']}")

        results[name] = {
            "overall": overall_metrics,
            "station_wise": station_metrics,
        }

    with open(BASELINES_RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n[INFO] Baseline results saved to {BASELINES_RESULTS_PATH}")


if __name__ == "__main__":
    main()
