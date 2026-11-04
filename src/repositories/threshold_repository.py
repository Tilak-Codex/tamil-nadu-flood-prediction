"""
Threshold repository for querying and managing CWC flood thresholds.
"""

from datetime import datetime, timezone
from typing import List, Optional
import pandas as pd
from sqlalchemy.orm import Session
from src.database.models import FloodThreshold
from src.config import CWC_THRESHOLDS_PATH


class ThresholdRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[FloodThreshold]:
        return self.db.query(FloodThreshold).order_by(FloodThreshold.station_id).all()

    def get_by_station(self, station_id: int) -> Optional[FloodThreshold]:
        return self.db.query(FloodThreshold).filter(FloodThreshold.station_id == station_id).first()

    def count(self) -> int:
        return self.db.query(FloodThreshold).count()

    def seed_from_csv(self) -> int:
        if self.count() > 0 or not CWC_THRESHOLDS_PATH.exists():
            return self.count()

        df = pd.read_csv(CWC_THRESHOLDS_PATH)
        thresholds_to_add = []
        for _, row in df.iterrows():
            sid = int(row["station_id"])
            item = FloodThreshold(
                station_id=sid,
                warning_level=float(row["warning_level"]) if pd.notna(row.get("warning_level")) else None,
                danger_level=float(row["danger_level"]) if pd.notna(row.get("danger_level")) else None,
                hfl=float(row["hfl"]) if pd.notna(row.get("hfl")) else None,
                status=str(row.get("status", "UNAVAILABLE")),
                source=str(row.get("source", "UNAVAILABLE")),
                updated_at=datetime.now(timezone.utc),
            )
            thresholds_to_add.append(item)

        self.db.bulk_save_objects(thresholds_to_add)
        self.db.commit()
        return len(thresholds_to_add)
