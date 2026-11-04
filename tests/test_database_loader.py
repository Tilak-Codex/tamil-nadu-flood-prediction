from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.data.loader import CSVDataLoader
from src.database.connection import Base
from src.database.models import Observation, Station


def test_database_fallback_skips_weather_only_observations(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'observations.db'}")
    Base.metadata.create_all(bind=engine)
    test_session = sessionmaker(bind=engine)
    monkeypatch.setattr("src.database.connection.SessionLocal", test_session)

    with test_session() as db:
        db.add(Station(station_id=1, station_name="Test Station", river="River", basin="Basin"))
        db.flush()
        timestamp = datetime(2026, 11, 5)
        db.add_all(
            [
                Observation(
                    station_id=1,
                    timestamp=timestamp,
                    water_level=10.0,
                    data_source="CWC_TELEMETRY",
                    data_type="HISTORICAL",
                ),
                Observation(
                    station_id=1,
                    timestamp=timestamp + timedelta(minutes=15),
                    water_level=None,
                    data_source="OPEN_METEO_LIVE",
                    data_type="OBSERVED",
                ),
                Observation(
                    station_id=1,
                    timestamp=timestamp + timedelta(hours=1),
                    water_level=11.0,
                    data_source="CWC_TELEMETRY",
                    data_type="HISTORICAL",
                ),
            ]
        )
        db.commit()

    loader = CSVDataLoader(cleaned_path=tmp_path / "missing.csv")
    observations = loader.get_station_data(1, recent_n=24)

    assert observations["water_level"].tolist() == [10.0, 11.0]
    assert observations["timestamp"].is_monotonic_increasing
    engine.dispose()
