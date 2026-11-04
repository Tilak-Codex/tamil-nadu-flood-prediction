"""
Station repository for database queries and seed management.
"""

from typing import List, Optional
import pandas as pd
from sqlalchemy.orm import Session

from src.database.models import Station, FloodThreshold
from src.config import STATION_LOOKUP_PATH, CWC_THRESHOLDS_PATH


class StationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[Station]:
        return self.db.query(Station).order_by(Station.station_id).all()

    def get_by_id(self, station_id: int) -> Optional[Station]:
        return self.db.query(Station).filter(Station.station_id == station_id).first()

    def count(self) -> int:
        return self.db.query(Station).count()

    def seed_from_csv(self) -> int:
        """Seeds the stations table from station_lookup.csv and cwc_thresholds.csv if empty."""
        if self.count() > 0:
            return self.count()

        if not STATION_LOOKUP_PATH.exists():
            return 0

        lookup_df = pd.read_csv(STATION_LOOKUP_PATH)
        thresholds_df = pd.read_csv(CWC_THRESHOLDS_PATH) if CWC_THRESHOLDS_PATH.exists() else pd.DataFrame()

        if not thresholds_df.empty:
            merged = lookup_df.merge(thresholds_df, on="station_id", how="left", suffixes=("", "_thresh"))
        else:
            merged = lookup_df

        stations_to_add = []
        thresholds_to_add = []
        for _, row in merged.iterrows():
            sid = int(row["station_id"])
            wl = float(row["warning_level"]) if pd.notna(row.get("warning_level")) else None
            dl = float(row["danger_level"]) if pd.notna(row.get("danger_level")) else None
            hfl = float(row["hfl"]) if pd.notna(row.get("hfl")) else None
            status = str(row.get("status", "UNAVAILABLE"))
            source = str(row.get("source", "UNAVAILABLE"))

            stn = Station(
                station_id=sid,
                station_name=str(row.get("Station", f"Station {sid}")).strip(),
                river=str(row.get("River", "Cauvery")).strip(),
                basin=str(row.get("Basin", "Cauvery")).strip(),
                latitude=float(row["Latitude"]) if pd.notna(row.get("Latitude")) else None,
                longitude=float(row["Longitude"]) if pd.notna(row.get("Longitude")) else None,
                rl_zero_gauge=float(row["RL_of_zeroGauge"]) if pd.notna(row.get("RL_of_zeroGauge")) else None,
                mean_sea_level=float(row["MeanSeaLevel"]) if pd.notna(row.get("MeanSeaLevel")) else None,
                warning_level=wl,
                danger_level=dl,
                hfl=hfl,
                threshold_status=status,
                threshold_source=source,
            )
            stations_to_add.append(stn)

            thresholds_to_add.append(
                FloodThreshold(
                    station_id=sid,
                    warning_level=wl,
                    danger_level=dl,
                    hfl=hfl,
                    status=status,
                    source=source,
                )
            )

        self.db.bulk_save_objects(stations_to_add)
        self.db.bulk_save_objects(thresholds_to_add)
        self.db.commit()
        return len(stations_to_add)
