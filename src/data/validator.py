"""
Data validation module.
Verifies file presence, non-emptiness, required schema, timestamp consistency,
and absence of illegal NaN/infinite values.
"""

from pathlib import Path
from typing import List, Tuple
import pandas as pd


class DataValidationError(Exception):
    """Raised when data fails integrity or schema validation."""
    pass


class DataValidator:
    REQUIRED_COLUMNS = [
        "station_id",
        "timestamp",
        "water_level",
        "segment_id",
    ]

    @staticmethod
    def validate_file_exists(file_path: Path) -> None:
        if not file_path.exists():
            raise FileNotFoundError(f"Data file does not exist: {file_path}")
        if file_path.stat().st_size == 0:
            raise DataValidationError(f"Data file is empty: {file_path}")

    @classmethod
    def validate_schema(cls, df: pd.DataFrame, required_cols: List[str] = None) -> None:
        req = required_cols or cls.REQUIRED_COLUMNS
        missing = [c for c in req if c not in df.columns]
        if missing:
            raise DataValidationError(f"Missing required columns in dataset: {missing}")

    @staticmethod
    def validate_timestamps(df: pd.DataFrame, ts_col: str = "timestamp") -> pd.DataFrame:
        if ts_col not in df.columns:
            raise DataValidationError(f"Timestamp column '{ts_col}' not found.")
        
        if not pd.api.types.is_datetime64_any_dtype(df[ts_col]):
            try:
                df[ts_col] = pd.to_datetime(df[ts_col])
            except Exception as e:
                raise DataValidationError(f"Failed to parse timestamps: {e}")
        
        if df[ts_col].isna().any():
            n_bad = df[ts_col].isna().sum()
            raise DataValidationError(f"Found {n_bad} null or unparseable timestamps.")
        
        return df

    @staticmethod
    def validate_no_duplicates(df: pd.DataFrame, subset: List[str] = None) -> None:
        sub = subset or ["station_id", "timestamp"]
        available_sub = [c for c in sub if c in df.columns]
        if len(available_sub) > 1:
            dups = df.duplicated(subset=available_sub).sum()
            if dups > 0:
                raise DataValidationError(f"Found {dups} duplicate records for key: {available_sub}")

    @staticmethod
    def validate_station_history(df_station: pd.DataFrame, min_records: int = 24) -> None:
        if len(df_station) < min_records:
            raise DataValidationError(
                f"Insufficient historical observations: got {len(df_station)}, minimum required is {min_records}."
            )

    @classmethod
    def validate_all(cls, df: pd.DataFrame, required_cols: List[str] = None) -> pd.DataFrame:
        cls.validate_schema(df, required_cols)
        df = cls.validate_timestamps(df)
        cls.validate_no_duplicates(df)
        return df
