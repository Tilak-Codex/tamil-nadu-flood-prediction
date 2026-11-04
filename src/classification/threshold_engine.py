"""
Explainable Risk Classification Engine based on CWC thresholds.
Maps river water levels to deterministic risk categories:
NORMAL, WARNING, DANGER, CRITICAL.
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class RiskClassificationResult:
    station_id: int
    predicted_level: float
    risk_level: str
    reason: str
    warning_level: Optional[float]
    danger_level: Optional[float]
    hfl: Optional[float]
    threshold_status: str
    threshold_source: str


class ThresholdEngine:
    """Deterministic and explainable threshold evaluation."""

    @staticmethod
    def classify(
        station_id: int,
        predicted_level: float,
        warning_level: Optional[float],
        danger_level: Optional[float],
        hfl: Optional[float],
        threshold_status: str = "DUMMY_PLACEHOLDER",
        threshold_source: str = "DUMMY_STATISTICAL_PERCENTILE",
    ) -> RiskClassificationResult:
        level = float(predicted_level)

        # Handle unavailable threshold case
        if (
            warning_level is None
            or danger_level is None
            or threshold_status == "UNAVAILABLE"
        ):
            return RiskClassificationResult(
                station_id=station_id,
                predicted_level=level,
                risk_level="UNKNOWN",
                reason="Official or estimated CWC thresholds are unavailable for this station.",
                warning_level=warning_level,
                danger_level=danger_level,
                hfl=hfl,
                threshold_status="UNAVAILABLE",
                threshold_source="UNAVAILABLE",
            )

        wl = float(warning_level)
        dl = float(danger_level)
        hfl_val = float(hfl) if hfl is not None else float("inf")

        if level < wl:
            risk_level = "NORMAL"
            reason = (
                f"Predicted river level ({level:.2f} m) is below the configured "
                f"Warning Level ({wl:.2f} m)."
            )
        elif wl <= level < dl:
            risk_level = "WARNING"
            reason = (
                f"Predicted river level ({level:.2f} m) meets or exceeds Warning Level "
                f"({wl:.2f} m) but remains below Danger Level ({dl:.2f} m)."
            )
        elif dl <= level < hfl_val:
            risk_level = "DANGER"
            reason = (
                f"Predicted river level ({level:.2f} m) meets or exceeds Danger Level "
                f"({dl:.2f} m) but remains below Highest Flood Level ({hfl_val:.2f} m)."
            )
        else:
            risk_level = "CRITICAL"
            reason = (
                f"Predicted river level ({level:.2f} m) meets or exceeds the Highest "
                f"Flood Level ({hfl_val:.2f} m)."
            )

        return RiskClassificationResult(
            station_id=station_id,
            predicted_level=level,
            risk_level=risk_level,
            reason=reason,
            warning_level=wl,
            danger_level=dl,
            hfl=hfl_val if hfl is not None else None,
            threshold_status=threshold_status,
            threshold_source=threshold_source,
        )
