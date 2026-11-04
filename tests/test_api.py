"""
Integration tests for FastAPI REST endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from src.api.app import app

client = TestClient(app)


def test_serve_dashboard_frontend():
    response = client.get("/")
    assert response.status_code == 200
    assert "Tamil Nadu" in response.text
    assert "leaflet" in response.text.lower() or "map" in response.text.lower()


def test_get_map_summary_endpoint():
    response = client.get("/map-summary")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 35
    assert "latitude" in data[0]
    assert "longitude" in data[0]
    assert "risk_level" in data[0]
    assert "predicted_water_level_m" in data[0]


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["data_source"] == "CSV"


def test_get_all_stations():
    response = client.get("/stations")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 35
    assert data[0]["station_id"] == 0
    assert "station_name" in data[0]
    assert "threshold_status" in data[0]


def test_get_station_by_id():
    response = client.get("/stations/0")
    assert response.status_code == 200
    data = response.json()
    assert data["station_id"] == 0
    assert data["station_name"] == "AKKIHEBBAL"


def test_get_station_not_found():
    response = client.get("/stations/9999")
    assert response.status_code == 404


def test_get_observations():
    response = client.get("/observations/0?n=10")
    assert response.status_code == 200
    data = response.json()
    assert data["station_id"] == 0
    assert len(data["observations"]) == 10
    assert "water_level" in data["observations"][0]


def test_get_thresholds():
    response = client.get("/thresholds/0")
    assert response.status_code == 200
    data = response.json()
    assert data["station_id"] == 0
    assert data["status"] in ["DUMMY_PLACEHOLDER", "VERIFIED_CWC", "UNAVAILABLE"]


def test_get_forecast_endpoint():
    response = client.get("/forecast/0")
    assert response.status_code == 200
    data = response.json()
    assert data["station_id"] == 0
    assert "predicted_water_level_m" in data
    assert "risk_level" in data
    assert "action_recommendation" in data


def test_get_risk_endpoint():
    response = client.get("/risk/0")
    assert response.status_code == 200
    data = response.json()
    assert data["station_id"] == 0
    assert "risk_level" in data


def test_get_model_metrics_endpoint():
    response = client.get("/model/metrics")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_custom_forecast_post():
    # Provide dummy 24 readings
    readings = [{"timestamp": f"2026-01-01 {i:02d}:00:00", "water_level": 745.0 + i * 0.1} for i in range(24)]
    payload = {
        "station_id": 0,
        "sequence_length": 24,
        "readings": readings,
    }
    response = client.post("/forecast", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "predicted_water_level_m" in data
    assert "risk_level" in data
