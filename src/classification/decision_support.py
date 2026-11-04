"""
Deterministic Decision Support Engine.
Produces rule-based recommendations for flood mitigation, reservoir operations,
and civil defense authorities based on classified risk and trend dynamics.
"""

from typing import Dict, Optional


class DecisionSupportEngine:
    """Generates standardized actionable advisories for disaster management."""

    DISCLAIMER = (
        "Advisory Notice: This recommendation is generated for research decision-support "
        "and situational awareness. Official flood alerts and evacuation orders must be "
        "issued by the Central Water Commission (CWC) or Tamil Nadu State Disaster Management Authority (TNSDMA)."
    )

    RECOMMENDATIONS = {
        "NORMAL": (
            "Continue routine monitoring and standard data acquisition. "
            "Hydrologic parameters remain within normal operating ranges."
        ),
        "WARNING": (
            "Escalate telemetry inspection frequency to hourly checks. "
            "Notify local taluk disaster response officers and prepare downstream "
            "embankment surveillance patrols."
        ),
        "DANGER": (
            "Alert district revenue administration and Tamil Nadu Fire and Rescue Services. "
            "Pre-position inflatable boats and relief supplies in vulnerable riparian zones. "
            "Inspect vulnerable barrages, sluice gates, and bunds."
        ),
        "CRITICAL": (
            "Issue immediate high-priority flood alerts. Coordinate targeted evacuation "
            "of human settlements and livestock in designated flood inundation corridors. "
            "Activate multi-agency emergency response centers."
        ),
        "UNKNOWN": (
            "Maintain cautious observation. Threshold values for this station are currently "
            "unverified or unavailable. Refer directly to regional water resources department gauges."
        ),
    }

    @classmethod
    def get_recommendation(
        cls,
        risk_level: str,
        rate_of_change: Optional[float] = None,
    ) -> Dict[str, str]:
        base_rec = cls.RECOMMENDATIONS.get(risk_level, cls.RECOMMENDATIONS["UNKNOWN"])

        # Dynamically append surge advisory if river is rising rapidly (> 0.25 m/h)
        trend_note = ""
        if rate_of_change is not None and rate_of_change > 0.25:
            trend_note = (
                f" NOTE: River level is actively surging at +{rate_of_change:.2f} m/h; "
                f"rapid inundation possible before peak crest."
            )
        elif rate_of_change is not None and rate_of_change < -0.25:
            trend_note = (
                f" NOTE: Water level is receding at {rate_of_change:.2f} m/h; "
                f"monitor for residual bank erosion."
            )

        return {
            "risk_level": risk_level,
            "action_recommendation": base_rec + trend_note,
            "disclaimer": cls.DISCLAIMER,
        }
