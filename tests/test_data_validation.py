"""
Unit tests for data validation and schema integrity.
"""

import pytest
import pandas as pd
from src.data.loader import CSVDataLoader
from src.data.validator import DataValidator, DataValidationError
from src.config import NUMERIC_FEATURES, TARGET_COL


@pytest.fixture
def loader():
    return CSVDataLoader()


def test_station_lookup_validity(loader):
    lookup = loader.load_station_lookup()
    assert len(lookup) == 35, f"Expected 35 stations, got {len(lookup)}"
    assert "station_id" in lookup.columns
    assert "Station" in lookup.columns
    assert "Latitude" in lookup.columns
    assert "Longitude" in lookup.columns
    assert lookup["Latitude"].isna().sum() == 0


def test_cleaned_dataset_validity(loader):
    df = loader.load_cleaned_data()
    assert len(df) > 900000, f"Expected >900k rows, got {len(df)}"
    for col in NUMERIC_FEATURES:
        assert col in df.columns, f"Required feature '{col}' missing from dataset"
    assert df["water_level"].isna().sum() == 0, "Found unexpected NaN in water_level"
    assert df["timestamp"].isna().sum() == 0, "Found null timestamps"


def test_no_duplicate_timestamps(loader):
    df = loader.load_cleaned_data()
    # Check sample of stations for speed
    sample = df[df["station_id"].isin([0, 1, 2])]
    dups = sample.duplicated(subset=["station_id", "timestamp"]).sum()
    assert dups == 0, f"Found {dups} duplicate timestamp records"


def test_validator_detects_missing_columns():
    invalid_df = pd.DataFrame({"water_level": [1.0, 2.0]})
    with pytest.raises(DataValidationError):
        DataValidator.validate_schema(invalid_df, required_cols=["station_id", "timestamp", "water_level"])
