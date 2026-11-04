"""
Prediction repository for storing and retrieving model forecasts and risk assessments.
"""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.database.models import Prediction


class PredictionRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(
        self,
        station_id: int,
        target_timestamp: datetime,
        predicted_water_level: float,
        latest_observed_level: float,
        rate_of_change: float,
        severity: str,
        severity_reason: str,
        action_recommendation: str,
        forecast_horizon_hours: int = 1,
        model_version: str = "Functional_LSTM_With_Station_Embedding",
        input_quality_status: str = "VALID",
        generation_timestamp: Optional[datetime] = None,
    ) -> Prediction:
        pred = Prediction(
            station_id=station_id,
            generation_timestamp=generation_timestamp or datetime.now(timezone.utc),
            target_timestamp=target_timestamp,
            forecast_horizon_hours=forecast_horizon_hours,
            predicted_water_level=predicted_water_level,
            latest_observed_level=latest_observed_level,
            rate_of_change=rate_of_change,
            severity=severity,
            severity_reason=severity_reason,
            action_recommendation=action_recommendation,
            model_version=model_version,
            input_quality_status=input_quality_status,
        )
        self.db.add(pred)
        self.db.commit()
        return pred

    def get_latest(self, station_id: int) -> Optional[Prediction]:
        return (
            self.db.query(Prediction)
            .filter(Prediction.station_id == station_id)
            .order_by(desc(Prediction.generation_timestamp))
            .first()
        )

    def get_history(self, station_id: int, limit: int = 24) -> List[Prediction]:
        return (
            self.db.query(Prediction)
            .filter(Prediction.station_id == station_id)
            .order_by(desc(Prediction.generation_timestamp))
            .limit(limit)
            .all()
        )
