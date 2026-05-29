"""Simple one-variable sensitivity checks for the risk score."""

from __future__ import annotations

from typing import Any

import pandas as pd

from neo_ange.risk.scoring import RiskScorer
from neo_ange.simulation.schemas import PERTURBED_VARIABLES
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
        """Return score changes after lowering and raising each variable."""
        base = row.to_dict() if isinstance(row, pd.Series) else dict(row)
        variables = variables or list(PERTURBED_VARIABLES)
        results: list[dict[str, Any]] = []
        for variable in variables:
            if variable not in base:
                continue
            base_value = _to_float(base.get(variable))
            if base_value is None:
                continue
            low_value = base_value * (1.0 - perturbation_pct)
            high_value = base_value * (1.0 + perturbation_pct)
            low_row = dict(base, **{variable: low_value})
            high_row = dict(base, **{variable: high_value})
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
                    "score_low": low_score,
                    "score_high": high_score,
                    "absolute_effect": abs(float(high_score) - float(low_score)),
                    "direction": direction,
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
