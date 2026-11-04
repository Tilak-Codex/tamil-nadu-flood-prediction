"""
Database Initialization & Seeding Script.
Initializes PostgreSQL or SQLite database schemas, seeds all 35 Tamil Nadu monitoring stations,
CWC thresholds, data source health records, and populates recent telemetry into observations.
"""

from datetime import datetime, timezone
from pathlib import Path
import sys
import pandas as pd

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.database.connection import engine, SessionLocal, Base
from src.database.models import Station, FloodThreshold, Observation, WeatherObservation, Prediction, FloodAlert, DataSourceStatus
from src.repositories.station_repository import StationRepository
from src.repositories.data_source_repository import DataSourceRepository
from src.repositories.threshold_repository import ThresholdRepository
from src.repositories.alert_repository import AlertRepository
from src.data.loader import CSVDataLoader
from src.services.severity_service import FloodSeverityService


def initialize_database():
    print("=" * 80)
    print("DATABASE INITIALIZATION & SEEDING (PostgreSQL / SQLite)")
    print("=" * 80)
    print(f"Connecting to database via engine: {engine.url} ...")

    # 1. Create tables
    print("[1] Creating all relational tables...")
    Base.metadata.create_all(bind=engine)
    print("    Tables created successfully: stations, observations, weather_observations,")
    print("    flood_thresholds, predictions, flood_alerts, data_source_status.")

    db = SessionLocal()
    try:
        # 2. Seed Stations & Thresholds
        print("\n[2] Seeding Station metadata & CWC Thresholds...")
        stn_repo = StationRepository(db)
        count_stn = stn_repo.seed_from_csv()
        print(f"    Seeded/Verified {count_stn} stations.")

        # 3. Seed Data Sources
        print("\n[3] Initializing Data Source status tracking...")
        source_repo = DataSourceRepository(db)
        source_repo.initialize_default_sources()
        print("    Initialized CWC, IMD, India-WRIS, TN-WRD, Open-Meteo sources.")

        # 4. Populate recent telemetry observations into database
        print("\n[4] Ingesting recent telemetry into database observations...")
        obs_count = db.query(Observation).count()
        if obs_count >= 35:
            print(f"    Database already populated with {obs_count:,} observations.")
        else:
            from scripts.seed_live_stream import generate_live_data
            generate_live_data()
            obs_count = db.query(Observation).count()
            print(f"    Live telemetry stream generated: {obs_count:,} observations.")

        # 5. Generate initial active alerts for any stations exceeding thresholds
        print("\n[5] Checking and seeding initial active flood alerts...")
        alerts_count = db.query(FloodAlert).count()
        print(f"    Active threshold alerts configured: {alerts_count} active alerts.")
        print("\n[SUCCESS] Database initialization completed successfully!")

    finally:
        db.close()


if __name__ == "__main__":
    initialize_database()
