"""Shared risk-priority schema constants."""

from __future__ import annotations

RISK_SCORE_VERSION = "risk-score-v0.1.0"

COMPONENT_COLUMNS = [
    "physical_risk_component",
    "orbital_risk_component",
    "approach_risk_component",
    "sentry_risk_component",
    "uncertainty_risk_component",
    "data_quality_component",
]

DEFAULT_COMPONENT_WEIGHTS: dict[str, float] = {
    "physical_risk_component": 0.22,
    "orbital_risk_component": 0.25,
    "approach_risk_component": 0.18,
    "sentry_risk_component": 0.17,
    "uncertainty_risk_component": 0.13,
    "data_quality_component": 0.05,
}

RISK_SCORE_COLUMNS = [
    "risk_score",
    "risk_score_0_100",
    *COMPONENT_COLUMNS,
    "risk_category",
    "risk_explanation_short",
    "scored_at_utc",
    "score_version",
]
