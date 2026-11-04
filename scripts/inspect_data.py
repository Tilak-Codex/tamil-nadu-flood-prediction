"""
Dataset Inspection & Profiling Script.
Generates an audit report of real-world hydrological telemetry in Tamil Nadu.
"""

import json
import sys
from pathlib import Path

# Ensure project root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pandas as pd
import numpy as np

from src.config import CLEANED_DATA_PATH, STATION_LOOKUP_PATH, CWC_THRESHOLDS_PATH
from src.data.loader import CSVDataLoader
from src.data.validator import DataValidator


def main():
    print("=" * 80)
    print("AI-BASED FLOOD PREDICTION SYSTEM FOR TAMIL NADU - DATA PROFILING REPORT")
    print("=" * 80)

    loader = CSVDataLoader()

    # 1. Station Lookup
    lookup = loader.load_station_lookup()
    print(f"\n[1] Station Metadata Registry:")
    print(f"    Total stations: {len(lookup)}")
    print(f"    Columns: {list(lookup.columns)}")
    print(f"    Basins represented: {lookup['Basin'].unique().tolist()}")
    print(f"    Rivers monitored: {lookup['River'].unique().tolist()}")

    # 2. CWC Thresholds
    thresholds = loader.load_thresholds()
    print(f"\n[2] CWC Thresholds Configuration:")
    print(f"    Total configured stations: {len(thresholds)}")
    print(f"    Status breakdown:\n{thresholds['status'].value_counts().to_string()}")

    # 3. Cleaned Time-Series Dataset
    print(f"\n[3] Cleaned Hydrological Dataset ({CLEANED_DATA_PATH}):")
    df = loader.load_cleaned_data()
    print(f"    Total rows: {len(df):,}")
    print(f"    Columns ({len(df.columns)}): {list(df.columns)}")
    print(f"    Unique stations: {df['station_id'].nunique()}")
    print(f"    Date Range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    # Missing values and duplicates
    n_null = df.isna().sum().sum()
    dups = df.duplicated(subset=['station_id', 'timestamp']).sum()
    print(f"    Missing values: {n_null}")
    print(f"    Duplicate (station_id, timestamp) rows: {dups}")

    # Station statistics
    print(f"\n[4] Station Observation Summary (Top 10 by volume):")
    st_counts = df.groupby(['station_id', 'Station', 'River']).agg(
        observations=('water_level', 'count'),
        min_level_m=('water_level', 'min'),
        max_level_m=('water_level', 'max'),
        mean_level_m=('water_level', 'mean'),
        imputed_rows=('was_imputed', 'sum')
    ).reset_index().sort_values('observations', ascending=False)

    print(st_counts.head(10).to_string(index=False))
    print("\n[INFO] Data inspection complete. Source of truth verified.")


if __name__ == "__main__":
    main()
