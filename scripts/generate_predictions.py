"""
Batch Prediction & Decision Support CSV Generation Script.
Applies the trained LSTM and CWC classification engine across unseen test sequences
to produce data/results/predictions.csv and data/results/risk_assessments.csv.
"""

import pickle
import sys
from pathlib import Path

# Ensure project root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import numpy as np
import pandas as pd
import tensorflow as tf

from src.config import (
    LSTM_MODEL_PATH,
    SCALERS_PATH,
    PREDICTIONS_CSV_PATH,
    RISK_ASSESSMENTS_CSV_PATH,
    LOOKBACK,
    FORECAST_HORIZON,
    NUMERIC_FEATURES,
    TARGET_COL,
)
from src.data.loader import CSVDataLoader
from src.preprocessing.sequence_builder import prepare_dataset_sequences
from src.classification.threshold_engine import ThresholdEngine
from src.classification.decision_support import DecisionSupportEngine


def main():
    print("=" * 80)
    print("GENERATING TEST PREDICTIONS & RISK ASSESSMENTS")
    print("=" * 80)

    loader = CSVDataLoader()
    df = loader.load_cleaned_data()
    lookup = loader.load_station_lookup()
    thresholds = loader.load_thresholds()

    if not LSTM_MODEL_PATH.exists() or not SCALERS_PATH.exists():
        print("[ERROR] Model artifacts not found. Run scripts/train_lstm.py first.")
        return

    print("[1] Loading model and scalers...")
    model = tf.keras.models.load_model(LSTM_MODEL_PATH)
    with open(SCALERS_PATH, "rb") as f:
        scalers = pickle.load(f)

    print("[2] Building test sequences...")
    _, _, test_data, _ = prepare_dataset_sequences(
        df,
        sequence_length=LOOKBACK,
        horizon=FORECAST_HORIZON,
        feature_cols=NUMERIC_FEATURES,
    )
    X_test, y_test, sid_test, ts_test = test_data

    print(f"    Evaluating {len(X_test):,} test sequences...")
    preds_scaled = model.predict(
        {"sequence_input": X_test, "station_input": sid_test},
        batch_size=512,
        verbose=1,
    ).flatten()

    target_idx = NUMERIC_FEATURES.index(TARGET_COL)
    predictions_rows = []
    risk_rows = []

    # Map station lookup and threshold info for fast dictionary lookup
    lookup_dict = lookup.set_index("station_id")["Station"].to_dict()
    thresh_dict = thresholds.set_index("station_id").to_dict(orient="index")

    print("[3] Transforming to real meters and computing CWC classifications...")
    for sid in np.unique(sid_test):
        mask = (sid_test == sid)
        if not np.any(mask):
            continue
        scaler = scalers[int(sid)]
        st_name = lookup_dict.get(sid, f"Station_{sid}").strip()
        t_info = thresh_dict.get(sid, {})

        dummy_true = np.zeros((np.sum(mask), len(NUMERIC_FEATURES)))
        dummy_pred = np.zeros((np.sum(mask), len(NUMERIC_FEATURES)))
        dummy_true[:, target_idx] = y_test[mask]
        dummy_pred[:, target_idx] = preds_scaled[mask]

        st_true_real = scaler.inverse_transform(dummy_true)[:, target_idx]
        st_pred_real = scaler.inverse_transform(dummy_pred)[:, target_idx]

        st_timestamps = [ts_test[i] for i, m in enumerate(mask) if m]

        wl = t_info.get("warning_level")
        dl = t_info.get("danger_level")
        hfl = t_info.get("hfl")
        t_status = t_info.get("status", "UNAVAILABLE")
        t_source = t_info.get("source", "UNAVAILABLE")

        for t_stamp, actual_m, pred_m in zip(st_timestamps, st_true_real, st_pred_real):
            # Classify risk
            risk_res = ThresholdEngine.classify(
                station_id=int(sid),
                predicted_level=pred_m,
                warning_level=wl,
                danger_level=dl,
                hfl=hfl,
                threshold_status=t_status,
                threshold_source=t_source,
            )

            # Decision support advisory
            advisory = DecisionSupportEngine.get_recommendation(
                risk_level=risk_res.risk_level
            )

            predictions_rows.append({
                "station_id": int(sid),
                "station_name": st_name,
                "timestamp": str(t_stamp),
                "actual_level_m": round(float(actual_m), 3),
                "predicted_level_m": round(float(pred_m), 3),
                "error_m": round(float(pred_m - actual_m), 3),
                "risk_level": risk_res.risk_level,
                "threshold_source": t_source,
            })

            risk_rows.append({
                "station_id": int(sid),
                "station_name": st_name,
                "timestamp": str(t_stamp),
                "predicted_level_m": round(float(pred_m), 3),
                "warning_level_m": risk_res.warning_level,
                "danger_level_m": risk_res.danger_level,
                "hfl_m": risk_res.hfl,
                "risk_level": risk_res.risk_level,
                "reason": risk_res.reason,
                "recommendation": advisory["action_recommendation"],
                "threshold_status": risk_res.threshold_status,
            })

    preds_df = pd.DataFrame(predictions_rows)
    risks_df = pd.DataFrame(risk_rows)

    loader.save_predictions(preds_df, PREDICTIONS_CSV_PATH)
    loader.save_risk_assessments(risks_df, RISK_ASSESSMENTS_CSV_PATH)

    print(f"\n[INFO] Saved {len(preds_df):,} test predictions to {PREDICTIONS_CSV_PATH}")
    print(f"[INFO] Saved {len(risks_df):,} risk assessments to {RISK_ASSESSMENTS_CSV_PATH}")
    print("\n--- RISK LEVEL FREQUENCY DISTRIBUTION ---")
    print(risks_df["risk_level"].value_counts().to_string())


if __name__ == "__main__":
    main()
