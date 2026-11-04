"""
Central configuration module for Flood Prediction and Decision Support System.
Uses project-relative paths and environment variable overrides.
"""

import os
from pathlib import Path

# Base project directory (e:\MiniProject\demo1)
BASE_DIR = Path(__file__).resolve().parent.parent

# Data Paths
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
THRESHOLDS_DIR = DATA_DIR / "thresholds"
RESULTS_DIR = DATA_DIR / "results"

CLEANED_DATA_PATH = PROCESSED_DATA_DIR / "cleaned_dataset.csv"
STATION_LOOKUP_PATH = PROCESSED_DATA_DIR / "station_lookup.csv"
CWC_THRESHOLDS_PATH = THRESHOLDS_DIR / "cwc_thresholds.csv"

# Result Paths
METRICS_CSV_PATH = RESULTS_DIR / "metrics.csv"
PREDICTIONS_CSV_PATH = RESULTS_DIR / "predictions.csv"
RISK_ASSESSMENTS_CSV_PATH = RESULTS_DIR / "risk_assessments.csv"

# Model Paths
MODELS_DIR = Path(os.getenv("MODELS_DIR", BASE_DIR / "models"))
LSTM_MODEL_DIR = MODELS_DIR / "lstm"
LSTM_MODEL_PATH = LSTM_MODEL_DIR / "model.keras"
SCALERS_PATH = LSTM_MODEL_DIR / "scalers.pkl"
METADATA_PATH = LSTM_MODEL_DIR / "metadata.json"
BASELINES_DIR = MODELS_DIR / "baselines"
BASELINES_RESULTS_PATH = BASELINES_DIR / "baseline_results.json"

# Results & Plots
PLOTS_DIR = BASE_DIR / "results" / "plots"

# Modeling Configuration
LOOKBACK = int(os.getenv("LOOKBACK", 24))  # 24 hourly observations (24 hours)
FORECAST_HORIZON = int(os.getenv("FORECAST_HORIZON", 1))  # 1 hour ahead
RANDOM_SEED = 42

# Train / Validation / Test Split (Chronological)
TRAIN_RATIO = float(os.getenv("TRAIN_RATIO", 0.70))
VAL_RATIO = float(os.getenv("VAL_RATIO", 0.15))
TEST_RATIO = float(os.getenv("TEST_RATIO", 0.15))

# Feature sets: 4 core hydrologic and meteorological features required by project specification
NUMERIC_FEATURES = [
    "water_level",
    "rainfall",
    "temperature",
    "pressure",
]
TARGET_COL = "water_level"
MONSOON_MONTHS = {6, 7, 8, 9}

# Training Hyperparameters
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 512))
EPOCHS = int(os.getenv("EPOCHS", 10))
LEARNING_RATE = float(os.getenv("LEARNING_RATE", 0.001))
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", 8))
PATIENCE = int(os.getenv("PATIENCE", 3))

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
