"""
Observation repository for database storage, retrieval, and deduplication of river and weather observations.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.database.models import Observation, WeatherObservation


class ObservationRepository:
    def __init__(self, db: Session):
        self.db = db

    def add_or_update(
        self,
        station_id: int,
        timestamp: datetime,
        water_level: Optional[float] = None,
        rainfall: Optional[float] = None,
        temperature: Optional[float] = None,
        pressure: Optional[float] = None,
        data_source: str = "OPEN_METEO",
        data_type: str = "OBSERVED",
        quality_status: str = "VALID",
    ) -> Observation:
        """Inserts a new observation or updates an existing matching (station_id, timestamp, data_type)."""
        existing = (
            self.db.query(Observation)
            .filter(
                Observation.station_id == station_id,
                Observation.timestamp == timestamp,
                Observation.data_type == data_type,
            )
            .first()
        )

        now = datetime.now(timezone.utc)
        if existing:
            if water_level is not None:
                existing.water_level = water_level
            if rainfall is not None:
                existing.rainfall = rainfall
            if temperature is not None:
                existing.temperature = temperature
            if pressure is not None:
                existing.pressure = pressure
            existing.data_source = data_source
            existing.quality_status = quality_status
            existing.fetched_at = now
            self.db.commit()
            return existing

        obs = Observation(
            station_id=station_id,
            timestamp=timestamp,
            water_level=water_level,
            rainfall=rainfall,
            temperature=temperature,
            pressure=pressure,
            data_source=data_source,
            data_type=data_type,
            quality_status=quality_status,
            fetched_at=now,
        )
        self.db.add(obs)

        # Also store into dedicated WeatherObservation if weather fields provided
        if rainfall is not None or temperature is not None or pressure is not None:
            weather_obs = WeatherObservation(
                station_id=station_id,
                timestamp=timestamp,
                rainfall=rainfall if rainfall is not None else 0.0,
                temperature=temperature if temperature is not None else 28.0,
                pressure=pressure if pressure is not None else 1010.0,
                data_source=data_source,
                data_type=data_type,
                quality_status=quality_status,
                fetched_at=now,
            )
            self.db.add(weather_obs)

        self.db.commit()
        return obs

    def get_latest(self, station_id: int) -> Optional[Observation]:
        """Returns the most recent observation for a station."""
        return (
            self.db.query(Observation)
            .filter(Observation.station_id == station_id)
            .order_by(desc(Observation.timestamp))
            .first()
        )

    def get_history(self, station_id: int, limit: int = 48) -> List[Observation]:
        """Returns the most recent observations up to limit in chronological order."""
        subquery = (
            self.db.query(Observation)
            .filter(Observation.station_id == station_id)
            .order_by(desc(Observation.timestamp))
            .limit(limit)
            .all()
        )
        return list(reversed(subquery))

    def get_weather_history(self, station_id: int, limit: int = 48) -> List[WeatherObservation]:
        """Returns recent dedicated weather observations."""
        subquery = (
            self.db.query(WeatherObservation)
            .filter(WeatherObservation.station_id == station_id)
            .order_by(desc(WeatherObservation.timestamp))
            .limit(limit)
            .all()
        )
        return list(reversed(subquery))

    def count_for_station(self, station_id: int) -> int:
        return self.db.query(Observation).filter(Observation.station_id == station_id).count()
