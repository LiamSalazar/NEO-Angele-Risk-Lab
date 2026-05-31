"""Monte Carlo engine for approximate orbital perturbation scenarios."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import numpy as np

from neo_ange.orbital_simulation.elements import extract_elements
from neo_ange.orbital_simulation.metrics import summarize_orbital_scenarios
from neo_ange.orbital_simulation.perturbation import perturb_elements, uncertainty_score
from neo_ange.orbital_simulation.propagation import baseline_min_distance, simulate_min_distances
from neo_ange.orbital_simulation.schemas import OrbitalSimulationResult


class OrbitalMonteCarloEngine:
    """Run approximate orbital clone simulations for one object row."""

    def simulate_object(
        self,
        row: dict[str, Any],
        n_clones: int = 300,
        horizon_days: int = 3650,
        time_step_days: int = 10,
        random_state: int | None = 42,
    ) -> dict[str, Any]:
        """Simulate one object and return summary metrics."""
        elements, warnings = extract_elements(row)
        rng = np.random.default_rng(random_state)
        score = uncertainty_score(elements)
        baseline_distance, _baseline_day = baseline_min_distance(
            elements,
            horizon_days=horizon_days,
            time_step_days=time_step_days,
        )
        clones = perturb_elements(elements, n_clones=n_clones, rng=rng)
        min_distances, closest_days, trace = simulate_min_distances(
            clones,
            horizon_days=horizon_days,
            time_step_days=time_step_days,
        )
        metrics = summarize_orbital_scenarios(
            min_distances=min_distances,
            closest_days=closest_days,
            baseline_distance=baseline_distance,
            uncertainty_score=score,
        )
        result = OrbitalSimulationResult(
            object_key=str(row.get("object_key")),
            designation=_designation(row),
            risk_score_0_100=_optional_float(row.get("risk_score_0_100")),
            risk_category=_optional_str(row.get("risk_category")),
            n_clones=n_clones,
            horizon_days=horizon_days,
            time_step_days=time_step_days,
            baseline_min_distance_au=baseline_distance,
            simulated_min_distance_mean_au=metrics["mean"],
            simulated_min_distance_p05_au=metrics["p05"],
            simulated_min_distance_p50_au=metrics["p50"],
            simulated_min_distance_p95_au=metrics["p95"],
            closest_approach_day_mean=metrics["closest_mean"],
            closest_approach_day_p05=metrics["closest_p05"],
            closest_approach_day_p95=metrics["closest_p95"],
            dispersion_index=metrics["dispersion_index"],
            orbital_uncertainty_score=score,
            scenario_category=metrics["scenario_category"],
            interpretation=metrics["interpretation"],
            warnings=warnings,
            simulated_at_utc=datetime.now(UTC).isoformat(),
        )
        payload = result.to_dict()
        payload["distance_trace"] = {
            key: [float(value) for value in values.tolist()] for key, values in trace.items()
        }
        return payload


def _designation(row: dict[str, Any]) -> str | None:
    for key in ["des", "name", "full_name"]:
        value = row.get(key)
        if value is not None:
            return str(value)
    return None


def _optional_float(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if np.isnan(result):
        return None
    return result


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)
