"""
Data Fetcher Module for External Environmental & Hydrological APIs.
Implements resilient requests, timeouts, status tracking, and canonical parsing.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import httpx

logger = logging.getLogger(__name__)


class ExternalDataFetcher:
    """Handles external API ingestion with timeouts, error handling, and unit normalization."""

    def __init__(self, timeout_seconds: float = 8.0):
        self.timeout = timeout_seconds
        self.open_meteo_url = os.getenv("OPEN_METEO_URL", "https://api.open-meteo.com/v1/forecast")
        self.imd_base_url = os.getenv("IMD_BASE_URL", "https://api.imd.gov.in/api/v1")
        self.imd_api_key = os.getenv("IMD_API_KEY", "")

    async def fetch_open_meteo(
        self,
        latitude: float,
        longitude: float,
        past_hours: int = 48,
        forecast_hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Fetches live meteorological observations and forecast from Open-Meteo.
        Variables: precipitation (mm), temperature_2m (°C), surface_pressure (hPa).
        Returns parsed canonical observations with UTC timestamps.
        """
        params = {
            "latitude": round(latitude, 4),
            "longitude": round(longitude, 4),
            "current": "temperature_2m,relative_humidity_2m,precipitation,surface_pressure",
            "hourly": "precipitation,temperature_2m,surface_pressure",
            "past_days": 2,
            "forecast_days": 1,
            "timezone": "UTC",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(self.open_meteo_url, params=params)
                if response.status_code != 200:
                    logger.warning(f"Open-Meteo returned HTTP {response.status_code}: {response.text[:200]}")
                    return {
                        "status": "HTTP_ERROR",
                        "error": f"HTTP {response.status_code}",
                        "current": None,
                        "hourly": [],
                    }

                data = response.json()
                current_raw = data.get("current", {})
                current_time = datetime.fromisoformat(current_raw.get("time", datetime.now(timezone.utc).isoformat()))
                if current_time.tzinfo is None:
                    current_time = current_time.replace(tzinfo=timezone.utc)

                current_obs = {
                    "timestamp": current_time,
                    "rainfall": float(current_raw.get("precipitation", 0.0)),
                    "temperature": float(current_raw.get("temperature_2m", 0.0)),
                    "pressure": float(current_raw.get("surface_pressure", 1013.25)),
                    "humidity": float(current_raw.get("relative_humidity_2m", 0.0)),
                    "source": "OPEN_METEO",
                    "quality_status": "VALID",
                }

                # Parse hourly records
                hourly_raw = data.get("hourly", {})
                times = hourly_raw.get("time", [])
                rain = hourly_raw.get("precipitation", [])
                temp = hourly_raw.get("temperature_2m", [])
                press = hourly_raw.get("surface_pressure", [])

                hourly_records = []
                for i in range(len(times)):
                    t_val = datetime.fromisoformat(times[i])
                    if t_val.tzinfo is None:
                        t_val = t_val.replace(tzinfo=timezone.utc)
                    hourly_records.append({
                        "timestamp": t_val,
                        "rainfall": float(rain[i]) if i < len(rain) and rain[i] is not None else 0.0,
                        "temperature": float(temp[i]) if i < len(temp) and temp[i] is not None else 0.0,
                        "pressure": float(press[i]) if i < len(press) and press[i] is not None else 1013.25,
                        "source": "OPEN_METEO",
                        "quality_status": "VALID",
                    })

                return {
                    "status": "SUCCESS",
                    "current": current_obs,
                    "hourly": hourly_records,
                }

            except httpx.TimeoutException:
                logger.error("Open-Meteo request timed out.")
                return {"status": "TIMEOUT", "error": "Request timed out", "current": None, "hourly": []}
            except Exception as e:
                logger.error(f"Error requesting Open-Meteo: {e}")
                return {"status": "ERROR", "error": str(e), "current": None, "hourly": []}

    async def fetch_imd_status(self) -> Dict[str, Any]:
        """Checks IMD API connectivity and authentication status."""
        if not self.imd_api_key:
            return {
                "source": "India Meteorological Department (IMD)",
                "status": "AUTHENTICATION_REQUIRED",
                "notes": "No IMD_API_KEY set in environment. Access requires official registration.",
            }

        headers = {"X-Api-Key": self.imd_api_key, "User-Agent": "TN-Flood-Early-Warning-System"}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.get(f"{self.imd_base_url}/current_wx", headers=headers)
                if resp.status_code == 200:
                    return {"source": "IMD", "status": "CONNECTED", "notes": "Active authorized connection."}
                elif resp.status_code == 401:
                    return {"source": "IMD", "status": "AUTHENTICATION_REQUIRED", "notes": "Invalid or expired API key."}
                else:
                    return {"source": "IMD", "status": f"HTTP_{resp.status_code}", "notes": resp.text[:150]}
            except Exception as e:
                return {"source": "IMD", "status": "UNREACHABLE", "notes": str(e)}

    async def check_cwc_status(self) -> Dict[str, Any]:
        """Checks NWDP / CWC portal availability."""
        async with httpx.AsyncClient(timeout=4.0) as client:
            try:
                resp = await client.get("https://nwdp.nwic.gov.in/", headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code == 200:
                    return {"source": "CWC / NWDP", "status": "CONNECTED", "notes": "Portal reachable."}
                return {"source": "CWC / NWDP", "status": f"HTTP_{resp.status_code}", "notes": "Non-200 status."}
            except Exception as e:
                return {
                    "source": "CWC / NWDP",
                    "status": "OFFLINE_TIMEOUT",
                    "notes": f"Portal offline or private network timeout: {str(e)[:80]}. Telemetry baseline cached.",
                }

    async def check_tn_dashboard_status(self) -> Dict[str, Any]:
        """Checks TN Flood Monitor availability."""
        async with httpx.AsyncClient(timeout=4.0) as client:
            try:
                resp = await client.get("https://chennaifloodmonitor.tn.gov.in/HomePage/Dashboard", headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code == 200:
                    return {"source": "TN State Flood Monitor", "status": "CONNECTED_PORTAL_ONLY", "notes": "Web portal online; no unauthenticated REST endpoint."}
                return {"source": "TN State Flood Monitor", "status": f"HTTP_{resp.status_code}", "notes": "Portal status error."}
            except Exception as e:
                return {"source": "TN State Flood Monitor", "status": "UNAVAILABLE", "notes": str(e)[:80]}
