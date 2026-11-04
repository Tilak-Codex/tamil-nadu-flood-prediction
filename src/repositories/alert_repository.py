"""
Alert repository for managing active and acknowledged flood alerts.
"""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from src.database.models import FloodAlert


class AlertRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, limit: int = 100) -> List[FloodAlert]:
        return self.db.query(FloodAlert).order_by(FloodAlert.created_at.desc()).limit(limit).all()

    def get_active_alerts(self, limit: int = 50) -> List[FloodAlert]:
        return (
            self.db.query(FloodAlert)
            .filter(FloodAlert.is_active == True)
            .order_by(FloodAlert.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_by_station(self, station_id: int, limit: int = 20) -> List[FloodAlert]:
        return (
            self.db.query(FloodAlert)
            .filter(FloodAlert.station_id == station_id)
            .order_by(FloodAlert.created_at.desc())
            .limit(limit)
            .all()
        )

    def create_alert(
        self,
        station_id: int,
        severity: str,
        title: str,
        message: str,
        current_water_level: float,
        threshold_level: Optional[float] = None,
    ) -> FloodAlert:
        alert = FloodAlert(
            station_id=station_id,
            severity=severity,
            title=title,
            message=message,
            current_water_level=current_water_level,
            threshold_level=threshold_level,
            is_active=True,
            is_acknowledged=False,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def acknowledge_alert(self, alert_id: int, acknowledged_by: str = "Duty Officer") -> Optional[FloodAlert]:
        alert = self.db.query(FloodAlert).filter(FloodAlert.id == alert_id).first()
        if alert:
            alert.is_acknowledged = True
            alert.is_active = False
            alert.acknowledged_at = datetime.now(timezone.utc)
            alert.acknowledged_by = acknowledged_by
            self.db.commit()
            self.db.refresh(alert)
        return alert
