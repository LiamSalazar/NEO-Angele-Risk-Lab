from __future__ import annotations

from neo_ange.risk.explanations import RiskExplanationService


def test_explain_row_returns_main_drivers() -> None:
    explanation = RiskExplanationService().explain_row(
        {
            "object_key": "A",
            "risk_score_0_100": 66,
            "risk_category": "high",
            "orbital_risk_component": 0.82,
            "sentry_risk_component": 0.61,
            "physical_risk_component": 0.2,
            "approach_risk_component": 0.3,
            "uncertainty_risk_component": 0.4,
            "data_quality_component": 0.1,
            "feature_completeness_ratio": 0.9,
        }
    )

    assert explanation["main_drivers"]
    assert explanation["main_drivers"][0]["component"] == "orbital_risk_component"
    assert (
        "higher" not in explanation["technical_explanation"].lower() or explanation["risk_category"]
    )


def test_explanation_detects_limitations_and_avoids_official_alert_language() -> None:
    explanation = RiskExplanationService().explain_row(
        {
            "object_key": "B",
            "risk_score_0_100": 25,
            "risk_category": "moderate",
            "orbital_risk_component": 0.2,
            "feature_completeness_ratio": 0.3,
            "arc_length": 5,
            "n_obs_used": 3,
        }
    )
    combined = " ".join(
        [
            explanation["short_explanation"],
            explanation["technical_explanation"],
            " ".join(explanation["data_limitations"]),
        ]
    ).lower()

    assert explanation["data_limitations"]
    assert "will impact earth" not in combined
    assert "official alert" not in explanation["short_explanation"].lower()
