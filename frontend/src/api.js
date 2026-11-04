/**
 * API client service connecting to FastAPI backend
 */

const BASE_URL = '/api';

export async function fetchDashboardStats() {
  const res = await fetch(`${BASE_URL}/dashboard/stats`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchStations() {
  const res = await fetch(`${BASE_URL}/stations`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchStation(id) {
  const res = await fetch(`${BASE_URL}/stations/${id}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchObservations(stationId, n = 48) {
  const res = await fetch(`${BASE_URL}/observations/${stationId}?n=${n}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchWeatherObservations(stationId, n = 48) {
  const res = await fetch(`${BASE_URL}/observations/${stationId}/weather?n=${n}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchForecast(stationId) {
  const res = await fetch(`${BASE_URL}/forecast/${stationId}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function runPrediction(stationId) {
  const res = await fetch(`${BASE_URL}/predictions/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ station_id: stationId, sequence_length: 24 }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchRiskSummary() {
  const res = await fetch(`${BASE_URL}/risk/summary`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchAlerts() {
  const res = await fetch(`${BASE_URL}/alerts`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchAllAlerts() {
  const res = await fetch(`${BASE_URL}/alerts/all?limit=100`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function acknowledgeAlert(alertId, acknowledgedBy = 'Duty Officer') {
  const res = await fetch(`${BASE_URL}/alerts/${alertId}/acknowledge`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ acknowledged_by: acknowledgedBy }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchModelMetrics() {
  const res = await fetch(`${BASE_URL}/health`);
  // also fetch from top-level /model/metrics
  const metricRes = await fetch('/model/metrics');
  if (!metricRes.ok) throw new Error(`HTTP ${metricRes.status}`);
  return metricRes.json();
}

export async function fetchDataSources() {
  const res = await fetch(`${BASE_URL}/data-sources`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function refreshDataSources() {
  const res = await fetch(`${BASE_URL}/data-sources/refresh`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
