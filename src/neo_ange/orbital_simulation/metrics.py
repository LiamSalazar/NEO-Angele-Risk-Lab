"""Metrics for approximate orbital simulation outputs."""

from __future__ import annotations

from typing import Any

import numpy as np


def summarize_orbital_scenarios(
    min_distances: np.ndarray,
    closest_days: np.ndarray,
    baseline_distance: float | None,
    uncertainty_score: float,
) -> dict[str, Any]:
    """Summarize clone minima and assign scenario category."""
    if len(min_distances) == 0:
        return {
            "mean": None,
            "p05": None,
            "p50": None,
            "p95": None,
            "closest_mean": None,
            "closest_p05": None,
            "closest_p95": None,
            "dispersion_index": None,
            "scenario_category": "uncertain",
            "interpretation": "No clone distances were produced.",
        }
    p05 = float(np.quantile(min_distances, 0.05))
    p50 = float(np.quantile(min_distances, 0.50))
    p95 = float(np.quantile(min_distances, 0.95))
    dispersion = float((p95 - p05) / max(abs(p50), 1e-6))
    category = scenario_category(
        p05=p05, dispersion=dispersion, uncertainty_score=uncertainty_score
    )
    return {
        "mean": float(np.mean(min_distances)),
        "p05": p05,
        "p50": p50,
        "p95": p95,
        "closest_mean": float(np.mean(closest_days)),
        "closest_p05": float(np.quantile(closest_days, 0.05)),
        "closest_p95": float(np.quantile(closest_days, 0.95)),
        "dispersion_index": dispersion,
        "scenario_category": category,
        "interpretation": interpretation(category, p05, p50, p95, baseline_distance),
    }


def scenario_category(p05: float, dispersion: float, uncertainty_score: float) -> str:
    """Categorize approximate orbital scenario behavior."""
    if p05 <= 0.05 and (dispersion > 0.35 or uncertainty_score > 0.55):
        return "needs_review"
    if dispersion > 0.75 or uncertainty_score > 0.75:
        return "uncertain"
    if dispersion > 0.25:
        return "variable"
    return "stable"


def interpretation(
    category: str,
    p05: float,
    p50: float,
    p95: float,
    baseline_distance: float | None,
) -> str:
    """Human-readable interpretation for one orbital scenario summary."""
    baseline_text = "baseline distance unavailable"
    if baseline_distance is not None:
        baseline_text = f"baseline minimum distance is {baseline_distance:.4f} AU"
    if category == "stable":
        return (
            "This object shows stable approximate orbital scenario behavior under the "
            f"available perturbation model; p05/p50/p95 are {p05:.4f}/{p50:.4f}/{p95:.4f} AU and "
            f"{baseline_text}."
        )
    if category == "variable":
        return (
            "This object shows variable approximate orbital scenario behavior; clone minimum "
            f"distances spread across {p05:.4f} to {p95:.4f} AU."
        )
    if category == "needs_review":
        return (
            "This object has low-distance or high-dispersion clone scenarios and should be "
            "reviewed in context, without treating this approximate model as an alert."
        )
    return (
        "This object has uncertain approximate orbital scenario behavior because the available "
        "orbit-quality proxies create broad clone dispersion."
    )
