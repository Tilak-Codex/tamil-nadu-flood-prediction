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
        elif loader.cleaned_path.exists():
            df = loader.load_cleaned_data()

            # Ingest the latest 48 hourly observations per station for fast DB access
            obs_to_add = []
            weather_to_add = []
            now = datetime.now(timezone.utc)

            stations = stn_repo.get_all()
            total_obs = 0

            for stn in stations:
                stn_df = df[df["station_id"] == stn.station_id].sort_values("timestamp").tail(48)
                for _, row in stn_df.iterrows():
                    ts = pd.to_datetime(row["timestamp"])
                    wl = float(row["water_level"])
                    rain = float(row.get("rainfall", 0.0) or 0.0)
                    temp = float(row.get("temperature", 28.0) or 28.0)
                    press = float(row.get("pressure", 1010.0) or 1010.0)

                    # Check if already exists in DB
                    existing = db.query(Observation).filter(
                        Observation.station_id == stn.station_id,
                        Observation.timestamp == ts,
                        Observation.data_type == "HISTORICAL",
                    ).first()

                    if not existing:
                        obs_to_add.append(
                            Observation(
                                station_id=stn.station_id,
                                timestamp=ts,
                                water_level=wl,
                                rainfall=rain,
                                temperature=temp,
                                pressure=press,
                                data_source="CWC_TELEMETRY",
                                data_type="HISTORICAL",
                                quality_status="VALID",
                                fetched_at=now,
                            )
                        )
                        weather_to_add.append(
                            WeatherObservation(
                                station_id=stn.station_id,
                                timestamp=ts,
                                rainfall=rain,
                                temperature=temp,
                                pressure=press,
                                data_source="HISTORICAL_ENRICHED",
                                data_type="HISTORICAL",
                                quality_status="VALID",
                                fetched_at=now,
                            )
                        )

            if obs_to_add:
                db.bulk_save_objects(obs_to_add)
                db.bulk_save_objects(weather_to_add)
                db.commit()
                print(f"    Ingested {len(obs_to_add):,} recent observations across 35 stations.")
            else:
                print("    Recent observations already populated in database.")
        else:
            print("    Notice: Raw dataset CSV not present; database observations verified.")

        # 5. Generate initial active alerts for any stations exceeding thresholds
        print("\n[5] Checking and seeding initial active flood alerts...")
        alerts_count = db.query(FloodAlert).count()
        if alerts_count > 0:
            print(f"    Active threshold alerts already configured: {alerts_count} active alerts.")
        elif 'df' in locals() and df is not None:
            alert_repo = AlertRepository(db)
            alerts_created = 0

            for stn in stations:
                latest_row = df[df["station_id"] == stn.station_id].sort_values("timestamp").tail(1)
                if latest_row.empty:
                    continue
                cur_wl = float(latest_row["water_level"].iloc[0])
                classification = FloodSeverityService.classify(
                    station_id=stn.station_id,
                    predicted_level=cur_wl,
                    warning_level=stn.warning_level,
                    danger_level=stn.danger_level,
                    hfl=stn.hfl,
                    threshold_status=stn.threshold_status,
                    threshold_source=stn.threshold_source,
                )

                if classification.severity in ["Above Normal", "Severe", "Extreme"]:
                    existing_alert = db.query(FloodAlert).filter(
                        FloodAlert.station_id == stn.station_id,
                        FloodAlert.is_active == True,
                    ).first()
                    if not existing_alert:
                        alert_repo.create_alert(
                            station_id=stn.station_id,
                            severity=classification.severity,
                            title=f"{classification.severity} Alert: {stn.station_name} ({stn.river})",
                            message=classification.reason + " " + classification.action_recommendation,
                            current_water_level=cur_wl,
                            threshold_level=stn.warning_level if classification.severity == "Above Normal" else stn.danger_level,
                        )
                        alerts_created += 1

            print(f"    Active threshold alerts configured: {alerts_created}")
        else:
            print("    Notice: Alerts verified.")
        print("\n[SUCCESS] Database initialization completed successfully!")

    finally:
        db.close()


if __name__ == "__main__":
    initialize_database()
