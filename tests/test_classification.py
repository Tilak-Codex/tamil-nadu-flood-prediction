"""
Unit tests for CWC risk classification and decision support engine.
"""

from src.classification.threshold_engine import ThresholdEngine
from src.classification.decision_support import DecisionSupportEngine


def test_normal_risk_classification():
    res = ThresholdEngine.classify(
        station_id=1,
        predicted_level=50.0,
        warning_level=80.0,
        danger_level=90.0,
        hfl=100.0,
    )
    assert res.risk_level == "NORMAL"
    assert "below the configured Warning Level" in res.reason


def test_warning_risk_classification():
    res = ThresholdEngine.classify(
        station_id=1,
        predicted_level=82.5,
        warning_level=80.0,
        danger_level=90.0,
        hfl=100.0,
    )
    assert res.risk_level == "WARNING"
    assert "exceeds Warning Level" in res.reason


def test_danger_risk_classification():
    res = ThresholdEngine.classify(
        station_id=1,
        predicted_level=95.0,
        warning_level=80.0,
        danger_level=90.0,
        hfl=100.0,
    )
    assert res.risk_level == "DANGER"
    assert "exceeds Danger Level" in res.reason


def test_critical_risk_classification():
    res = ThresholdEngine.classify(
        station_id=1,
        predicted_level=105.0,
        warning_level=80.0,
        danger_level=90.0,
        hfl=100.0,
    )
    assert res.risk_level == "CRITICAL"
    assert "Highest Flood Level" in res.reason


def test_unavailable_threshold_classification():
    res = ThresholdEngine.classify(
        station_id=1,
        predicted_level=50.0,
        warning_level=None,
        danger_level=None,
        hfl=None,
        threshold_status="UNAVAILABLE",
    )
    assert res.risk_level == "UNKNOWN"
    assert res.threshold_status == "UNAVAILABLE"


def test_decision_support_recommendations():
    rec_normal = DecisionSupportEngine.get_recommendation("NORMAL")
    assert "routine monitoring" in rec_normal["action_recommendation"]

    rec_warning = DecisionSupportEngine.get_recommendation("WARNING", rate_of_change=0.35)
    assert "hourly checks" in rec_warning["action_recommendation"]
    assert "NOTE: River level is actively surging" in rec_warning["action_recommendation"]

    rec_critical = DecisionSupportEngine.get_recommendation("CRITICAL")
    assert "evacuation" in rec_critical["action_recommendation"]
