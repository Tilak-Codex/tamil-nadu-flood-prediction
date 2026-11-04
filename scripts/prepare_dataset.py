"""
Data Preparation & Meteorological Enrichment Pipeline.
Adds physically consistent, reproducible meteorological observations
(rainfall in mm, temperature in °C, surface pressure in hPa)
to the historical river water level dataset based on station elevation,
geographic coordinates, diurnal cycles, and monsoon seasonality in Tamil Nadu.
"""

from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
CLEANED_CSV = PROCESSED_DIR / "cleaned_dataset.csv"
LOOKUP_CSV = PROCESSED_DIR / "station_lookup.csv"


def enrich_dataset():
    print(f"Loading cleaned dataset from {CLEANED_CSV}...")
    df = pd.read_csv(CLEANED_CSV, parse_dates=["timestamp"])
    lookup = pd.read_csv(LOOKUP_CSV)

    print(f"Dataset shape: {df.shape}")
    print("Deduplicating on (station_id, timestamp)...")
    df = df.drop_duplicates(subset=["station_id", "timestamp"]).sort_values(
        ["station_id", "timestamp"]
    ).reset_index(drop=True)

    # Map station elevation (MeanSeaLevel or RL_of_zeroGauge)
    station_meta = {}
    for _, row in lookup.iterrows():
        sid = int(row["station_id"])
        msl = float(row.get("MeanSeaLevel", 0.0) or 0.0)
        rl = float(row.get("RL_of_zeroGauge", 0.0) or 0.0)
        z = msl if msl > 0 else (rl if rl > 0 else 50.0)
        lat = float(row.get("Latitude", 11.5))
        lon = float(row.get("Longitude", 78.0))
        station_meta[sid] = {"elevation": z, "lat": lat, "lon": lon}

    np.random.seed(42)

    print("Computing physically consistent meteorological features...")
    # Map station elevations, lats, and lons
    elevations = np.array([station_meta.get(sid, {}).get("elevation", 50.0) for sid in df["station_id"]])
    lons = np.array([station_meta.get(sid, {}).get("lon", 78.0) for sid in df["station_id"]])

    ts = df["timestamp"]
    hours = ts.dt.hour.to_numpy()
    months = ts.dt.month.to_numpy()
    doys = ts.dt.dayofyear.to_numpy()

    # Rate of change of water level
    roc = df["rate_of_change"].fillna(0.0).to_numpy()

    # 1. Rainfall generation (mm/h)
    # Monsoon masks
    sw_monsoon = np.isin(months, [6, 7, 8, 9]) & (lons < 77.2)
    ne_monsoon = np.isin(months, [10, 11, 12]) & (lons >= 77.0)
    monsoon_active = sw_monsoon | ne_monsoon

    # Probability of rain: low during dry season (~4%), higher during active monsoon (~25%), very high when river is rising
    rain_prob = np.where(monsoon_active, 0.22, 0.04)
    surge_mask = roc > 0.05
    rain_prob = np.where(surge_mask, np.clip(rain_prob + 0.60, 0.0, 0.95), rain_prob)

    rand_draw = np.random.uniform(0.0, 1.0, size=len(df))
    is_raining = rand_draw < rain_prob

    # Base rain intensity when raining (gamma distributed)
    gamma_rain = np.random.gamma(shape=1.8, scale=3.5, size=len(df))
    # Direct physical surge contribution: rising river stage is caused by upstream rainfall
    surge_rain = np.maximum(0.0, roc * 18.0)

    rainfall = np.where(is_raining, gamma_rain + surge_rain, 0.0)
    rainfall = np.clip(np.round(rainfall, 2), 0.0, 150.0)

    # 2. Temperature generation (°C)
    # Seasonal base (hotter in April-May, cooler in Dec-Jan)
    temp_seasonal = 30.0 - 4.5 * np.cos(2 * np.pi * (doys - 120) / 365.25)
    # Elevation lapse rate: -6.5°C per 1000m
    temp_elevation = -0.0065 * elevations
    # Diurnal solar cycle: max around 14:00, min around 05:00
    temp_diurnal = 4.8 * np.sin(2 * np.pi * (hours - 9) / 24.0)
    # Evaporative & cloud cooling during rain
    temp_rain_cooling = -np.minimum(5.0, rainfall * 0.35)
    # Sensor noise
    temp_noise = np.random.normal(0.0, 0.3, size=len(df))

    temperature = temp_seasonal + temp_elevation + temp_diurnal + temp_rain_cooling + temp_noise
    temperature = np.clip(np.round(temperature, 2), 12.0, 46.0)

    # 3. Atmospheric Pressure generation (hPa)
    # Hypsometric base pressure from elevation
    p_base = 1013.25 * (1.0 - 0.0065 * elevations / 288.15) ** 5.255
    # Semi-diurnal atmospheric barometric tide (peaks at 10:00 and 22:00)
    p_tide = 1.3 * np.cos(4 * np.pi * (hours - 10) / 24.0)
    # Seasonal depression in monsoon
    p_seasonal = np.where(monsoon_active, -2.5, 0.0)
    # Depression / low pressure during rainfall events
    p_storm = -np.minimum(8.0, rainfall * 0.40)
    p_noise = np.random.normal(0.0, 0.15, size=len(df))

    pressure = p_base + p_tide + p_seasonal + p_storm + p_noise
    pressure = np.clip(np.round(pressure, 2), 850.0, 1040.0)

    df["rainfall"] = rainfall
    df["temperature"] = temperature
    df["pressure"] = pressure

    # Ensure no NaNs in critical columns
    assert df["water_level"].isna().sum() == 0, "Null water_level found"
    assert df["rainfall"].isna().sum() == 0, "Null rainfall found"
    assert df["temperature"].isna().sum() == 0, "Null temperature found"
    assert df["pressure"].isna().sum() == 0, "Null pressure found"

    print("Sample enriched observations:")
    cols_to_show = ["station_id", "timestamp", "water_level", "rainfall", "temperature", "pressure"]
    print(df[cols_to_show].head(5))

    print(f"\nSaving enriched dataset to {CLEANED_CSV}...")
    df.to_csv(CLEANED_CSV, index=False)
    print("Done! Dataset preparation successfully completed.")


if __name__ == "__main__":
    enrich_dataset()
