"""
Data source health status repository for monitoring API connections, last fetch times, and error logs.
"""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from src.database.models import DataSourceStatus


class DataSourceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[DataSourceStatus]:
        return self.db.query(DataSourceStatus).all()

    def get_by_name(self, source_name: str) -> Optional[DataSourceStatus]:
        return self.db.query(DataSourceStatus).filter(DataSourceStatus.source_name == source_name).first()

    def update_status(
        self,
        source_name: str,
        status: str,
        last_successful_fetch: Optional[datetime] = None,
        latest_observation_time: Optional[datetime] = None,
        error_details: Optional[str] = None,
        update_frequency: str = "Hourly",
        api_endpoint: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> DataSourceStatus:
        existing = self.get_by_name(source_name)
        now = datetime.now(timezone.utc)
        if existing:
            existing.status = status
            if last_successful_fetch:
                existing.last_successful_fetch = last_successful_fetch
            if latest_observation_time:
                existing.latest_observation_time = latest_observation_time
            existing.error_details = error_details
            if api_endpoint:
                existing.api_endpoint = api_endpoint
            if notes:
                existing.notes = notes
            existing.updated_at = now
            self.db.commit()
            return existing

        new_status = DataSourceStatus(
            source_name=source_name,
            status=status,
            last_successful_fetch=last_successful_fetch,
            latest_observation_time=latest_observation_time,
            error_details=error_details,
            update_frequency=update_frequency,
            api_endpoint=api_endpoint,
            notes=notes,
            updated_at=now,
        )
        self.db.add(new_status)
        self.db.commit()
        return new_status

    def initialize_default_sources(self):
        """Initializes records for the 4 external sources investigated in the project."""
        defaults = [
            {
                "source_name": "Open-Meteo Weather API",
                "status": "CONNECTED",
                "update_frequency": "Hourly",
                "api_endpoint": "https://api.open-meteo.com/v1/forecast",
                "notes": "Public unauthenticated real-time hourly meteorological data (rainfall, temperature, pressure).",
            },
            {
                "source_name": "Central Water Commission (CWC / NWDP)",
                "status": "OFFLINE_TIMEOUT",
                "update_frequency": "Hourly Telemetry",
                "api_endpoint": "https://nwdp.nwic.gov.in/",
                "notes": "Portal endpoint offline or restricted; hourly verified CWC telemetry cached locally.",
            },
            {
                "source_name": "India Meteorological Department (IMD)",
                "status": "AUTHENTICATION_REQUIRED",
                "update_frequency": "Hourly / Daily",
                "api_endpoint": "https://api.imd.gov.in/api/v1/",
                "notes": "Requires registered X-Api-Key credential. Configurable via IMD_API_KEY environment variable.",
            },
            {
                "source_name": "TN State Flood Monitoring Dashboard",
                "status": "PORTAL_RESTRICTED",
                "update_frequency": "Real-Time Portal",
                "api_endpoint": "https://chennaifloodmonitor.tn.gov.in/",
                "notes": "Internal state disaster dashboard without public unauthenticated REST API.",
            },
        ]
        for item in defaults:
            if not self.get_by_name(item["source_name"]):
                self.update_status(
                    source_name=item["source_name"],
                    status=item["status"],
                    update_frequency=item["update_frequency"],
                    api_endpoint=item["api_endpoint"],
                    notes=item["notes"],
                )
