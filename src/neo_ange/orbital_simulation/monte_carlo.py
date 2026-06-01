"""Covariance-aware orbital scenario simulation engine."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import numpy as np

from neo_ange.orbital_simulation.covariance import parse_covariance_payload, sample_orbital_clones
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
        covariance_payload = parse_covariance_payload(row)
        clones, covariance_diagnostics = sample_orbital_clones(
            elements,
            covariance_payload,
            n_clones=n_clones,
            rng=rng,
        )
        simulation_method = "covariance_based"
        uncertainty_quality = "medium"
        fallback_reason = None
        if not clones:
            simulation_method = "heuristic_fallback"
            uncertainty_quality = "low"
            fallback_reason = "; ".join(covariance_diagnostics.get("warnings", [])) or (
                "No valid SBDB covariance matrix was available."
            )
            warnings.append(f"Covariance fallback used: {fallback_reason}")
            clones = perturb_elements(elements, n_clones=n_clones, rng=rng)
            covariance_diagnostics["valid_clone_count"] = int(n_clones)
            covariance_diagnostics["invalid_clone_count"] = 0
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
            valid_clone_count=int(
                covariance_diagnostics.get("valid_clone_count") or len(min_distances)
            ),
            invalid_clone_count=int(covariance_diagnostics.get("invalid_clone_count") or 0),
            covariance_available=bool(covariance_payload.get("available")),
            simulation_method=simulation_method,
            covariance_dimension=covariance_diagnostics.get("covariance_dimension"),
            covariance_epoch=_optional_str(covariance_payload.get("epoch")),
            covariance_method=_optional_str(covariance_payload.get("form")) or "sbdb_covariance",
            fallback_reason=fallback_reason,
            uncertainty_quality=uncertainty_quality,
            propagator="two_body_kepler_approximation",
            horizon_days=horizon_days,
            time_step_days=time_step_days,
            baseline_min_distance_au=baseline_distance,
            simulated_min_distance_mean_au=metrics["mean"],
            simulated_min_distance_std_au=metrics["std"],
            simulated_min_distance_p05_au=metrics["p05"],
            simulated_min_distance_p50_au=metrics["p50"],
            simulated_min_distance_p95_au=metrics["p95"],
            closest_approach_day_mean=metrics["closest_mean"],
            closest_approach_day_p05=metrics["closest_p05"],
            closest_approach_day_p95=metrics["closest_p95"],
            dispersion_index=metrics["dispersion_index"],
            orbital_uncertainty_score=score,
            scenario_category=metrics["scenario_category"],
            cad_validation_available=_cad_distance(row) is not None,
            cad_validation_error_au=_cad_validation_error(baseline_distance, row),
            interpretation=metrics["interpretation"],
            warnings=[*warnings, *covariance_diagnostics.get("warnings", [])],
            simulated_at_utc=datetime.now(UTC).isoformat(),
        )
        payload = result.to_dict()
        payload["distance_trace"] = {
            key: [float(value) for value in values.tolist()] for key, values in trace.items()
        }
        payload["possible_resolution_miss"] = bool(time_step_days > 5)
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


def _cad_distance(row: dict[str, Any]) -> float | None:
    for key in ("min_close_approach_dist", "min_close_approach_dist_min"):
        value = _optional_float(row.get(key))
        if value is not None:
            return value
    return None


def _cad_validation_error(baseline_distance: float | None, row: dict[str, Any]) -> float | None:
    cad_distance = _cad_distance(row)
    if baseline_distance is None or cad_distance is None:
        return None
    return float(abs(float(baseline_distance) - cad_distance))
