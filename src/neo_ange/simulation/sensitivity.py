"""Deterministic one-variable sensitivity checks for the risk score."""

from __future__ import annotations

from typing import Any

import pandas as pd

from neo_ange.risk.scoring import RiskScorer
from neo_ange.simulation.schemas import PERTURBED_VARIABLES
from neo_ange.simulation.uncertainty import refresh_derived_features
from neo_ange.utils.serialization import to_jsonable


class SensitivityAnalyzer:
    """Estimate approximate score sensitivity by perturbing one variable at a time."""

    def __init__(self, risk_scorer: RiskScorer | None = None) -> None:
        self.risk_scorer = risk_scorer or RiskScorer()

    def estimate_feature_sensitivity(
        self,
        row: dict[str, Any] | pd.Series,
        variables: list[str] | None = None,
        perturbation_pct: float = 0.1,
    ) -> list[dict[str, Any]]:
        """Return score changes after deterministic sweeps of base variables."""
        raw_base = row.to_dict() if isinstance(row, pd.Series) else dict(row)
        base = _with_refreshed_derived(raw_base)
        variables = variables or list(PERTURBED_VARIABLES)
        results: list[dict[str, Any]] = []
        base_score = self.risk_scorer.score_row(base)["risk_score_0_100"]
        for variable in variables:
            if variable not in base:
                continue
            base_value = _to_float(base.get(variable))
            if base_value is None:
                continue
            low_value = _swept_value(variable, base_value, -perturbation_pct)
            high_value = _swept_value(variable, base_value, perturbation_pct)
            low_row = _with_refreshed_derived(base, variable, low_value)
            high_row = _with_refreshed_derived(base, variable, high_value)
            low_score = self.risk_scorer.score_row(low_row)["risk_score_0_100"]
            high_score = self.risk_scorer.score_row(high_row)["risk_score_0_100"]
            direction = "mixed_or_low_effect"
            if low_score > high_score:
                direction = "increases_risk_when_lower"
            elif high_score > low_score:
                direction = "increases_risk_when_higher"
            results.append(
                {
                    "variable": variable,
                    "base_value": base_value,
                    "low_value": low_value,
                    "high_value": high_value,
                    "base_score": base_score,
                    "score_low": low_score,
                    "score_high": high_score,
                    "delta_low": float(low_score) - float(base_score),
                    "delta_high": float(high_score) - float(base_score),
                    "absolute_effect": abs(float(high_score) - float(low_score)),
                    "direction": direction,
                    "analysis_mode": "deterministic_sensitivity",
                }
            )
        results.sort(key=lambda item: item["absolute_effect"], reverse=True)
        return to_jsonable(results)

    def top_sensitivity_factors(
        self,
        row: dict[str, Any] | pd.Series,
        variables: list[str] | None = None,
        perturbation_pct: float = 0.1,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Return the top sensitivity factors by absolute score effect."""
        return self.estimate_feature_sensitivity(row, variables, perturbation_pct)[:limit]


def _to_float(value: Any) -> float | None:
    try:
        if value is None or value is pd.NA:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _swept_value(variable: str, base_value: float, perturbation_pct: float) -> float:
    if variable == "condition_code":
        return float(round(min(max(base_value + perturbation_pct * 9.0, 0.0), 9.0)))
    if variable == "sentry_ip":
        return float(min(max(base_value * (1.0 + perturbation_pct), 0.0), 1.0))
    if base_value == 0 and perturbation_pct > 0:
        return 0.01
    return max(base_value * (1.0 + perturbation_pct), 0.0)


def _with_refreshed_derived(
    base: dict[str, Any],
    variable: str | None = None,
    value: float | None = None,
) -> dict[str, Any]:
    row = dict(base)
    if variable is not None:
        row[variable] = value
    frame = pd.DataFrame([row])
    refreshed = refresh_derived_features(frame)
    return refreshed.iloc[0].to_dict()
