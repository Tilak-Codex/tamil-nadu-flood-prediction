"""
CSV Data Access Layer.
Isolates all CSV reading and writing operations. Enables future swap to
PostgreSQL or other databases without altering service or ML logic.
"""

from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

from src.config import (
    CLEANED_DATA_PATH,
    STATION_LOOKUP_PATH,
    CWC_THRESHOLDS_PATH,
    METRICS_CSV_PATH,
    PREDICTIONS_CSV_PATH,
    RISK_ASSESSMENTS_CSV_PATH,
)
from src.data.validator import DataValidator, DataValidationError


class CSVDataLoader:
    """Encapsulates all file I/O for the flood forecasting system."""

    def __init__(
        self,
        cleaned_path: Path = CLEANED_DATA_PATH,
        lookup_path: Path = STATION_LOOKUP_PATH,
        thresholds_path: Path = CWC_THRESHOLDS_PATH,
    ):
        self.cleaned_path = Path(cleaned_path)
        self.lookup_path = Path(lookup_path)
        self.thresholds_path = Path(thresholds_path)
        self._cached_cleaned: Optional[pd.DataFrame] = None
        self._cached_lookup: Optional[pd.DataFrame] = None
        self._cached_thresholds: Optional[pd.DataFrame] = None

    def load_station_lookup(self, force_reload: bool = False) -> pd.DataFrame:
        if self._cached_lookup is None or force_reload:
            DataValidator.validate_file_exists(self.lookup_path)
            df = pd.read_csv(self.lookup_path)
            DataValidator.validate_schema(df, ["station_id", "Station", "River", "Latitude", "Longitude"])
            self._cached_lookup = df
        return self._cached_lookup.copy()

    def load_thresholds(self, force_reload: bool = False) -> pd.DataFrame:
        if self._cached_thresholds is None or force_reload:
            DataValidator.validate_file_exists(self.thresholds_path)
            df = pd.read_csv(self.thresholds_path)
            DataValidator.validate_schema(
                df, ["station_id", "warning_level", "danger_level", "hfl", "status", "source"]
            )
            self._cached_thresholds = df
        return self._cached_thresholds.copy()

    def load_cleaned_data(self, force_reload: bool = False) -> pd.DataFrame:
        if self._cached_cleaned is None or force_reload:
            DataValidator.validate_file_exists(self.cleaned_path)
            df = pd.read_csv(self.cleaned_path, parse_dates=["timestamp"])
            df = DataValidator.validate_all(df)
            self._cached_cleaned = df
        return self._cached_cleaned.copy()

    def get_station_data(self, station_id: int, recent_n: Optional[int] = None) -> pd.DataFrame:
        """Retrieves observations for a specific station, sorted chronologically."""
        df = self.load_cleaned_data()
        st_df = df[df["station_id"] == station_id].sort_values("timestamp")
        if st_df.empty:
            raise DataValidationError(f"Station ID {station_id} not found in observation dataset.")
        if recent_n is not None:
            st_df = st_df.tail(recent_n)
        return st_df.reset_index(drop=True)

    def get_station_metadata(self, station_id: int) -> Dict:
        """Retrieves static metadata and threshold info for a given station."""
        lookup = self.load_station_lookup()
        st_meta = lookup[lookup["station_id"] == station_id]
        if st_meta.empty:
            raise DataValidationError(f"Station ID {station_id} not found in metadata registry.")
        meta_dict = st_meta.iloc[0].to_dict()

        # Merge threshold info if available
        thresholds = self.load_thresholds()
        st_thresh = thresholds[thresholds["station_id"] == station_id]
        if not st_thresh.empty:
            t_row = st_thresh.iloc[0].to_dict()
            meta_dict.update({
                "warning_level": t_row.get("warning_level"),
                "danger_level": t_row.get("danger_level"),
                "hfl": t_row.get("hfl"),
                "threshold_status": t_row.get("status", "UNAVAILABLE"),
                "threshold_source": t_row.get("source", "UNAVAILABLE"),
            })
        else:
            meta_dict.update({
                "warning_level": None,
                "danger_level": None,
                "hfl": None,
                "threshold_status": "UNAVAILABLE",
                "threshold_source": "UNAVAILABLE",
            })
        return meta_dict

    def save_metrics(self, df_metrics: pd.DataFrame, path: Path = METRICS_CSV_PATH) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        df_metrics.to_csv(path, index=False)
        return path

    def save_predictions(self, df_preds: pd.DataFrame, path: Path = PREDICTIONS_CSV_PATH) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        df_preds.to_csv(path, index=False)
        return path

    def save_risk_assessments(self, df_risks: pd.DataFrame, path: Path = RISK_ASSESSMENTS_CSV_PATH) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        df_risks.to_csv(path, index=False)
        return path
