"""
Comparative Model Evaluation Script.
Merges baseline and LSTM performance into a unified data/results/metrics.csv.
"""

import json
import sys
from pathlib import Path

# Ensure project root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pandas as pd

from src.config import (
    BASELINES_RESULTS_PATH,
    METADATA_PATH,
    METRICS_CSV_PATH,
)
from src.data.loader import CSVDataLoader


def main():
    print("=" * 80)
    print("COMPARATIVE MODEL EVALUATION & METRICS GENERATION")
    print("=" * 80)

    rows = []

    # 1. Load Baseline Results
    if BASELINES_RESULTS_PATH.exists():
        with open(BASELINES_RESULTS_PATH, "r") as f:
            baselines_data = json.load(f)
        for model_name, res in baselines_data.items():
            overall = res["overall"]
            rows.append({
                "station_id": -1,
                "station": "OVERALL",
                "model": model_name,
                "mae": overall["mae"],
                "rmse": overall["rmse"],
                "r2": overall["r2"],
                "nse": overall["nse"],
                "samples": overall["samples"],
            })
            for sid_str, st_res in res.get("station_wise", {}).items():
                rows.append({
                    "station_id": int(sid_str),
                    "station": st_res.get("station_name", f"Station_{sid_str}"),
                    "model": model_name,
                    "mae": st_res["mae"],
                    "rmse": st_res["rmse"],
                    "r2": st_res["r2"],
                    "nse": st_res["nse"],
                    "samples": st_res["samples"],
                })

    # 2. Load LSTM Results
    if METADATA_PATH.exists():
        with open(METADATA_PATH, "r") as f:
            lstm_meta = json.load(f)
        overall = lstm_meta["overall_test_metrics"]
        rows.append({
            "station_id": -1,
            "station": "OVERALL",
            "model": "LSTM_Shared_Embedding",
            "mae": overall["mae"],
            "rmse": overall["rmse"],
            "r2": overall["r2"],
            "nse": overall["nse"],
            "samples": overall["samples"],
        })
        for sid_str, st_res in lstm_meta.get("station_wise_metrics", {}).items():
            rows.append({
                "station_id": int(sid_str),
                "station": st_res.get("station_name", f"Station_{sid_str}"),
                "model": "LSTM_Shared_Embedding",
                "mae": st_res["mae"],
                "rmse": st_res["rmse"],
                "r2": st_res["r2"],
                "nse": st_res["nse"],
                "samples": st_res["samples"],
            })

    if not rows:
        print("[ERROR] No evaluation results found. Please run train_baselines.py and train_lstm.py first.")
        return

    metrics_df = pd.DataFrame(rows)
    loader = CSVDataLoader()
    saved_path = loader.save_metrics(metrics_df, METRICS_CSV_PATH)
    print(f"\n[INFO] Saved complete metrics to {saved_path}")

    print("\n--- OVERALL MODEL COMPARISON ---")
    overall_df = metrics_df[metrics_df["station"] == "OVERALL"]
    print(overall_df[["model", "mae", "rmse", "r2", "nse", "samples"]].to_string(index=False))

    print("\n--- SAMPLE STATION-WISE COMPARISON (First 5 stations) ---")
    sample_stations = metrics_df[metrics_df["station_id"].isin([0, 1, 2, 3, 4])]
    print(sample_stations[["station_id", "station", "model", "rmse", "nse"]].to_string(index=False))


if __name__ == "__main__":
    main()
