"""
Leak-Free LSTM Model Training Pipeline.
Implements chronological train/val/test splitting, training-only scaler fitting,
functional Keras architecture with station embeddings, early stopping,
and comprehensive hydrologic evaluation on unseen test data.
"""

from datetime import datetime
import json
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pickle
import time
import numpy as np
import pandas as pd
import tensorflow as tf

from src.config import (
    LSTM_MODEL_DIR,
    LSTM_MODEL_PATH,
    SCALERS_PATH,
    METADATA_PATH,
    LOOKBACK,
    FORECAST_HORIZON,
    NUMERIC_FEATURES,
    TARGET_COL,
    BATCH_SIZE,
    EPOCHS,
    LEARNING_RATE,
    EMBEDDING_DIM,
    PATIENCE,
    RANDOM_SEED,
)
from src.data.loader import CSVDataLoader
from src.preprocessing.sequence_builder import prepare_dataset_sequences
from src.models.lstm_model import build_shared_lstm_model
from src.evaluation.metrics import evaluate_forecasts


def main():
    print("=" * 80)
    print("TRAINING MULTI-STATION LSTM MODEL (LEAK-FREE)")
    print("=" * 80)

    # Set reproducible random seeds
    tf.keras.utils.set_random_seed(RANDOM_SEED)

    LSTM_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    loader = CSVDataLoader()
    df = loader.load_cleaned_data()
    lookup = loader.load_station_lookup()

    num_stations = int(lookup["station_id"].max()) + 1

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

    # Save scalers fitted ONLY on training data
    with open(SCALERS_PATH, "wb") as f:
        pickle.dump(scalers, f)
    print(f"    Saved {len(scalers)} station scalers (fitted only on train partition) to {SCALERS_PATH}")

    # Build model architecture
    print("\n[2] Assembling LSTM Neural Network architecture...")
    model = build_shared_lstm_model(
        sequence_length=LOOKBACK,
        num_numeric_features=len(NUMERIC_FEATURES),
        num_stations=num_stations,
        embedding_dim=EMBEDDING_DIM,
        learning_rate=LEARNING_RATE,
    )
    model.summary()

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=PATIENCE,
            restore_best_weights=True,
            verbose=1,
        ),
        tf.keras.callbacks.ModelCheckpoint(
            filepath=str(LSTM_MODEL_PATH),
            monitor="val_loss",
            save_best_only=True,
            verbose=1,
        ),
    ]

    print(f"\n[3] Fitting model (Epochs: {EPOCHS}, Batch Size: {BATCH_SIZE})...")
    start_time = time.time()
    history = model.fit(
        {"sequence_input": X_train, "station_input": sid_train},
        y_train,
        validation_data=({"sequence_input": X_val, "station_input": sid_val}, y_val),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=callbacks,
        verbose=1,
    )
    elapsed = time.time() - start_time
    print(f"    Training completed in {elapsed:.2f} seconds.")

    # Save training history for plotting
    history_dict = {k: [float(v) for v in vals] for k, vals in history.history.items()}
    history_path = LSTM_MODEL_DIR / "training_history.json"
    with open(history_path, "w") as f:
        json.dump(history_dict, f, indent=2)

    # 4. Comprehensive Evaluation on unseen test split
    print("\n[4] Evaluating LSTM on unseen test sequences...")
    preds_scaled = model.predict(
        {"sequence_input": X_test, "station_input": sid_test},
        batch_size=BATCH_SIZE * 2,
        verbose=0,
    ).flatten()

    target_idx = NUMERIC_FEATURES.index(TARGET_COL)
    y_test_real = np.zeros_like(y_test)
    preds_real = np.zeros_like(preds_scaled)

    station_metrics = {}
    for sid in np.unique(sid_test):
        mask = sid_test == sid
        if not np.any(mask):
            continue
        scaler = scalers[int(sid)]

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
    print(f"\n    Overall LSTM -> MAE: {overall_metrics['mae']} m, RMSE: {overall_metrics['rmse']} m, R2: {overall_metrics['r2']}, NSE: {overall_metrics['nse']}")

    metadata = {
        "model_type": "Functional_LSTM_With_Station_Embedding",
        "training_timestamp": datetime.now().isoformat(),
        "training_duration_seconds": round(elapsed, 2),
        "lookback_observations": LOOKBACK,
        "forecast_horizon_observations": FORECAST_HORIZON,
        "features": NUMERIC_FEATURES,
        "target": TARGET_COL,
        "train_samples": len(X_train),
        "val_samples": len(X_val),
        "test_samples": len(X_test),
        "hyperparameters": {
            "epochs": EPOCHS,
            "batch_size": BATCH_SIZE,
            "learning_rate": LEARNING_RATE,
            "embedding_dim": EMBEDDING_DIM,
            "patience": PATIENCE,
        },
        "overall_test_metrics": overall_metrics,
        "station_wise_metrics": station_metrics,
    }

    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"[INFO] Saved model checkpoint to {LSTM_MODEL_PATH}")
    print(f"[INFO] Saved metadata to {METADATA_PATH}")


if __name__ == "__main__":
    main()
