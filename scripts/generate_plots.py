"""
Research Visualization & Plot Generator.
Creates 7 high-resolution research figures saved in results/plots/:
1. Actual vs Predicted River Level
2. Training vs Validation Loss Curve
3. Prediction Error Distribution (Residuals)
4. Historical River-Level Time Series
5. Hydrologic Dynamics: Rate of Change vs River Level
6. Station-wise Model Performance (RMSE & NSE Comparison)
7. Risk Classification Timeline with CWC Thresholds
"""

import json
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.config import (
    PLOTS_DIR,
    PREDICTIONS_CSV_PATH,
    RISK_ASSESSMENTS_CSV_PATH,
    METRICS_CSV_PATH,
    LSTM_MODEL_DIR,
    CLEANED_DATA_PATH,
)

# Apply consistent aesthetic theme
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["font.size"] = 10


def plot_01_actual_vs_predicted(preds_df: pd.DataFrame, out_path: Path):
    """Plot 1: Actual vs Predicted River Level on a representative test slice."""
    plt.figure(figsize=(12, 5), dpi=300)
    # Pick station 0 (Akkihebbal) or station with dynamic hydrograph
    sample_df = preds_df[preds_df["station_id"] == 0].tail(200).copy()
    sample_df["timestamp"] = pd.to_datetime(sample_df["timestamp"])
    
    plt.plot(sample_df["timestamp"], sample_df["actual_level_m"], label="Actual Level (m)", color="#1f77b4", lw=2)
    plt.plot(sample_df["timestamp"], sample_df["predicted_level_m"], label="LSTM Forecast (m)", color="#d62728", ls="--", lw=2)
    
    st_name = sample_df["station_name"].iloc[0]
    plt.title(f"Figure 1: Actual vs Predicted River Level (Station: {st_name})", fontsize=13, fontweight="bold")
    plt.xlabel("Timestamp", fontsize=11)
    plt.ylabel("Water Level (m above datum)", fontsize=11)
    plt.legend(frameon=True)
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    print(f"    Saved: {out_path.name}")


def plot_02_loss_curve(history_path: Path, out_path: Path):
    """Plot 2: Training vs Validation Loss Curve."""
    plt.figure(figsize=(9, 5), dpi=300)
    if history_path.exists():
        with open(history_path, "r") as f:
            hist = json.load(f)
        epochs = range(1, len(hist["loss"]) + 1)
        plt.plot(epochs, hist["loss"], label="Training Loss (MSE)", color="#2ca02c", lw=2)
        plt.plot(epochs, hist["val_loss"], label="Validation Loss (MSE)", color="#ff7f0e", lw=2)
        plt.title("Figure 2: Neural Network Loss Progression (Training vs Validation)", fontsize=13, fontweight="bold")
        plt.xlabel("Epoch", fontsize=11)
        plt.ylabel("Mean Squared Error (Scaled)", fontsize=11)
        plt.legend(frameon=True)
    else:
        plt.text(0.5, 0.5, "Training History Not Found", ha="center", va="center")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    print(f"    Saved: {out_path.name}")


def plot_03_error_distribution(preds_df: pd.DataFrame, out_path: Path):
    """Plot 3: Prediction Residual Distribution (Histogram & KDE)."""
    plt.figure(figsize=(9, 5), dpi=300)
    errors = preds_df["error_m"].dropna()
    # Filter extreme outliers for clean visualization
    p01, p99 = errors.quantile(0.01), errors.quantile(0.99)
    filtered_errors = errors[(errors >= p01) & (errors <= p99)]

    sns.histplot(filtered_errors, kde=True, color="#9467bd", bins=50, stat="density")
    plt.axvline(0, color="black", linestyle="--", lw=1.5, label="Zero Bias Line")
    plt.axvline(filtered_errors.mean(), color="red", linestyle=":", lw=1.5, label=f"Mean Error ({filtered_errors.mean():.3f} m)")
    plt.title("Figure 3: Prediction Residual Distribution (y_pred - y_true)", fontsize=13, fontweight="bold")
    plt.xlabel("Forecast Error (m)", fontsize=11)
    plt.ylabel("Density", fontsize=11)
    plt.legend(frameon=True)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    print(f"    Saved: {out_path.name}")


def plot_04_historical_timeseries(cleaned_path: Path, out_path: Path):
    """Plot 4: Multi-Station Historical River-Level Time Series."""
    plt.figure(figsize=(13, 6), dpi=300)
    df = pd.read_csv(cleaned_path, parse_dates=["timestamp"])
    stations_to_plot = [0, 1, 14, 16]  # Akkihebbal, Bhavani Bridge, Mettur, Musiri
    
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
    for sid, color in zip(stations_to_plot, colors):
        subset = df[df["station_id"] == sid].set_index("timestamp").resample("1D")["water_level"].mean()
        st_name = df.loc[df["station_id"] == sid, "Station"].iloc[0].strip()
        plt.plot(subset.index, subset.values, label=f"{st_name} (ID: {sid})", color=color, lw=1.5, alpha=0.85)

    plt.title("Figure 4: Historical Multi-Year Daily River Level Trajectories in Tamil Nadu", fontsize=13, fontweight="bold")
    plt.xlabel("Year", fontsize=11)
    plt.ylabel("Water Level (m)", fontsize=11)
    plt.legend(frameon=True, loc="upper right")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    print(f"    Saved: {out_path.name}")


def plot_05_rate_of_change(cleaned_path: Path, out_path: Path):
    """Plot 5: Hydrologic Dynamics - Rate of Change vs Water Level."""
    plt.figure(figsize=(10, 5), dpi=300)
    df = pd.read_csv(cleaned_path)
    sample = df[df["station_id"] == 0].sample(n=min(5000, len(df[df["station_id"] == 0])), random_state=42)
    
    plt.scatter(sample["water_level"], sample["rate_of_change"], alpha=0.3, color="#17becf", edgecolors="none", s=20)
    plt.axhline(0, color="gray", linestyle="--", lw=1)
    plt.title("Figure 5: Phase Portrait - Rate of Change (m/h) vs Water Level (Station: Akkihebbal)", fontsize=13, fontweight="bold")
    plt.xlabel("Water Level (m)", fontsize=11)
    plt.ylabel("Rate of Change (m/h)", fontsize=11)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    print(f"    Saved: {out_path.name}")


def plot_06_station_performance(metrics_path: Path, out_path: Path):
    """Plot 6: Station-wise Model Comparison (RMSE & NSE)."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), dpi=300, sharex=True)
    if metrics_path.exists():
        df = pd.read_csv(metrics_path)
        station_df = df[df["station_id"].between(0, 15)].copy()
        
        # Filter models of interest
        models = ["Persistence_Naive", "Moving_Average_24h", "LSTM_Shared_Embedding"]
        sub = station_df[station_df["model"].isin(models)]
        
        sns.barplot(data=sub, x="station", y="rmse", hue="model", ax=ax1, palette="Set2")
        ax1.set_title("Figure 6: Station-Wise Model Comparison — RMSE (Lower is Better)", fontsize=12, fontweight="bold")
        ax1.set_ylabel("RMSE (m)")
        ax1.legend(loc="upper left")

        # NSE plot (clipped for visualization)
        sub_nse = sub.copy()
        sub_nse["nse_clipped"] = sub_nse["nse"].clip(lower=-1.0, upper=1.0)
        sns.barplot(data=sub_nse, x="station", y="nse_clipped", hue="model", ax=ax2, palette="Set2")
        ax2.set_title("Station-Wise Model Comparison — NSE (Higher is Better, clipped [-1, 1])", fontsize=12, fontweight="bold")
        ax2.set_ylabel("Nash-Sutcliffe Efficiency")
        ax2.set_xticklabels(ax2.get_xticklabels(), rotation=45, ha="right")
        ax2.legend(loc="lower left")

    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    print(f"    Saved: {out_path.name}")


def plot_07_risk_timeline(risks_path: Path, out_path: Path):
    """Plot 7: Risk Classification Timeline with CWC Warning and Danger Thresholds."""
    plt.figure(figsize=(13, 5), dpi=300)
    if risks_path.exists():
        df = pd.read_csv(risks_path)
        sample = df[df["station_id"] == 0].tail(150).copy()
        sample["timestamp"] = pd.to_datetime(sample["timestamp"])

        plt.plot(sample["timestamp"], sample["predicted_level_m"], label="Predicted River Level (m)", color="#1f77b4", lw=2)
        
        wl = sample["warning_level_m"].iloc[0]
        dl = sample["danger_level_m"].iloc[0]
        hfl = sample["hfl_m"].iloc[0]

        if pd.notna(wl):
            plt.axhline(wl, color="#e67e22", linestyle="--", label=f"Warning Level ({wl:.2f} m)")
        if pd.notna(dl):
            plt.axhline(dl, color="#c0392b", linestyle="-.", label=f"Danger Level ({dl:.2f} m)")
        if pd.notna(hfl) and hfl < 2500:
            plt.axhline(hfl, color="#8e44ad", linestyle=":", label=f"HFL ({hfl:.2f} m)")

        # Shade risk regions
        risk_colors = {"NORMAL": "#2ecc71", "WARNING": "#f39c12", "DANGER": "#e74c3c", "CRITICAL": "#8e44ad"}
        for r_level, color in risk_colors.items():
            mask = sample["risk_level"] == r_level
            if mask.any():
                plt.scatter(sample.loc[mask, "timestamp"], sample.loc[mask, "predicted_level_m"],
                            color=color, s=30, label=f"Risk: {r_level}", zorder=4)

        st_name = sample["station_name"].iloc[0]
        plt.title(f"Figure 7: Flood Risk Assessment Timeline with CWC Thresholds ({st_name})", fontsize=13, fontweight="bold")
        plt.xlabel("Timestamp", fontsize=11)
        plt.ylabel("Water Level (m)", fontsize=11)
        plt.xticks(rotation=30)
        plt.legend(frameon=True, bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    print(f"    Saved: {out_path.name}")


def main():
    print("=" * 80)
    print("GENERATING RESEARCH VISUALIZATIONS & PLOTS")
    print("=" * 80)

    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    preds_df = pd.read_csv(PREDICTIONS_CSV_PATH) if PREDICTIONS_CSV_PATH.exists() else None
    history_path = LSTM_MODEL_DIR / "training_history.json"

    if preds_df is not None:
        plot_01_actual_vs_predicted(preds_df, PLOTS_DIR / "01_actual_vs_predicted.png")
        plot_03_error_distribution(preds_df, PLOTS_DIR / "03_error_distribution.png")
    else:
        print("[SKIP] Plot 1 & 3: predictions.csv not found yet.")

    plot_02_loss_curve(history_path, PLOTS_DIR / "02_loss_curve.png")

    if CLEANED_DATA_PATH.exists():
        plot_04_historical_timeseries(CLEANED_DATA_PATH, PLOTS_DIR / "04_historical_timeseries.png")
        plot_05_rate_of_change(CLEANED_DATA_PATH, PLOTS_DIR / "05_rate_of_change_vs_level.png")

    if METRICS_CSV_PATH.exists():
        plot_06_station_performance(METRICS_CSV_PATH, PLOTS_DIR / "06_station_performance_comparison.png")

    if RISK_ASSESSMENTS_CSV_PATH.exists():
        plot_07_risk_timeline(RISK_ASSESSMENTS_CSV_PATH, PLOTS_DIR / "07_risk_classification_timeline.png")

    print("\n[INFO] All research plots successfully saved to results/plots/")


if __name__ == "__main__":
    main()
