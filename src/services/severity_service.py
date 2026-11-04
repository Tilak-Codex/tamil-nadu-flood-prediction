"""
Flood Severity Classification & Decision Support Service.
Implements the 5 canonical project categories:
  - Normal
  - Above Normal
  - Severe
  - Extreme
  - Threshold Unavailable
Provides deterministic, explainable civil defense recommendations and disclaimers.
"""

from typing import Dict, Optional, Tuple, NamedTuple


class SeverityResult(NamedTuple):
    severity: str
    severity_color: str
    basis: str
    reason: str
    action_recommendation: str
    disclaimer: str
    warning_level: Optional[float]
    danger_level: Optional[float]
    hfl: Optional[float]
    threshold_status: str
    threshold_source: str


class FloodSeverityService:
    DISCLAIMER = (
        "ACADEMIC / RESEARCH DECISION SUPPORT PROTOTYPE ONLY: "
        "These automated risk classifications and recommendations are computer-generated forecasts "
        "and do NOT constitute official civil defense alerts or governmental emergency instructions. "
        "Always consult the Central Water Commission (CWC), State Disaster Management Authority (TNDRMD), "
        "and local district administration for verified evacuation advisories."
    )

    RECOMMENDATIONS = {
        "Normal": "Continue routine water-level monitoring. River stage remains within standard channel margins.",
        "Above Normal": "Increase monitoring frequency and verify recent upstream gauge telemetry and local rainfall reports.",
        "Severe": "Notify the responsible regional water resources and disaster monitoring teams. Verify official CWC bulletins.",
        "Extreme": "Urgently verify the hydrological situation with official district authorities and strictly follow emergency instructions.",
        "Threshold Unavailable": "Flood severity cannot be determined due to missing official station gauge thresholds. Consult official CWC / TNDRMD bulletins directly.",
    }

    SEVERITY_COLORS = {
        "Normal": "#10b981",              # Green
        "Above Normal": "#eab308",        # Yellow
        "Severe": "#f97316",              # Orange
        "Extreme": "#ef4444",             # Red
        "Threshold Unavailable": "#6b7280" # Gray
    }

    @classmethod
    def classify(
        cls,
        station_id: int,
        predicted_level: float,
        warning_level: Optional[float] = None,
        danger_level: Optional[float] = None,
        hfl: Optional[float] = None,
        threshold_status: Optional[str] = None,
        threshold_source: Optional[str] = None,
        rate_of_change: float = 0.0,
    ) -> SeverityResult:
        """
        Classifies future river water level against station-specific thresholds.
        Returns severity category, explanation, and non-authoritative advisory.
        """
        t_status = (threshold_status or "UNAVAILABLE").upper()
        t_source = threshold_source or "UNAVAILABLE"

        # If threshold is unavailable or sentinel placeholder is unverified
        if t_status == "UNAVAILABLE" or warning_level is None or danger_level is None:
            return SeverityResult(
                severity="Threshold Unavailable",
                severity_color=cls.SEVERITY_COLORS["Threshold Unavailable"],
                basis="Missing official station gauge thresholds in registry.",
                reason="Official CWC warning and danger levels are not configured for this station.",
                action_recommendation=cls.RECOMMENDATIONS["Threshold Unavailable"],
                disclaimer=cls.DISCLAIMER,
                warning_level=warning_level,
                danger_level=danger_level,
                hfl=hfl,
                threshold_status=t_status,
                threshold_source=t_source,
            )

        # Build basis description
        is_placeholder = "DUMMY" in t_status or "PLACEHOLDER" in t_status
        basis_desc = (
            "Project-defined statistical percentile threshold (unverified research placeholder)"
            if is_placeholder
            else f"Official verified station thresholds ({t_source})"
        )

        # Compute extreme boundary: HFL if present, otherwise danger_level + buffer
        extreme_threshold = hfl if (hfl is not None and hfl > danger_level) else danger_level + (danger_level - warning_level)

        # Classification logic
        if predicted_level < warning_level:
            severity = "Normal"
            reason = (
                f"Predicted water level ({predicted_level:.3f} m) is below the Warning Level ({warning_level:.3f} m). "
                f"Rate of change: {rate_of_change:+.3f} m/h."
            )
        elif warning_level <= predicted_level < danger_level:
            severity = "Above Normal"
            reason = (
                f"Predicted water level ({predicted_level:.3f} m) has crossed Warning Level ({warning_level:.3f} m) "
                f"but is below Danger Level ({danger_level:.3f} m)."
            )
        elif danger_level <= predicted_level < extreme_threshold:
            severity = "Severe"
            reason = (
                f"Predicted water level ({predicted_level:.3f} m) has crossed Danger Level ({danger_level:.3f} m) "
                f"approaching Extreme threshold ({extreme_threshold:.3f} m)."
            )
        else:
            severity = "Extreme"
            reason = (
                f"CRITICAL SURGE: Predicted water level ({predicted_level:.3f} m) exceeds Extreme threshold ({extreme_threshold:.3f} m)."
            )

        # Add rate of change note if rising rapidly (> 0.25 m/h)
        if rate_of_change > 0.25 and severity in ["Above Normal", "Severe", "Extreme"]:
            reason += f" River stage is surging rapidly at {rate_of_change:+.3f} m/h."

        return SeverityResult(
            severity=severity,
            severity_color=cls.SEVERITY_COLORS[severity],
            basis=basis_desc,
            reason=reason,
            action_recommendation=cls.RECOMMENDATIONS[severity],
            disclaimer=cls.DISCLAIMER,
            warning_level=round(warning_level, 3),
            danger_level=round(danger_level, 3),
            hfl=round(hfl, 3) if hfl is not None else None,
            threshold_status=t_status,
            threshold_source=t_source,
        )
