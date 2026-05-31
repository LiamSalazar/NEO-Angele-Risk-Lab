"""Orbital element perturbation rules for approximate clone generation."""

from __future__ import annotations

from typing import Any

import numpy as np


def uncertainty_score(elements: dict[str, Any]) -> float:
    """Return a bounded uncertainty proxy from available orbit-quality fields."""
    condition = _safe_float(elements.get("condition_code"), default=3.0)
    rms = _safe_float(elements.get("rms"), default=0.4)
    arc = _safe_float(elements.get("arc_length"), default=365.0)
    obs = _safe_float(elements.get("n_obs_used"), default=100.0)
    condition_part = min(max(condition, 0.0), 9.0) / 9.0
    rms_part = min(max(rms, 0.0), 2.0) / 2.0
    arc_part = 1.0 / (1.0 + max(arc, 0.0) / 365.0)
    obs_part = 1.0 / (1.0 + max(obs, 0.0) / 250.0)
    return float(
        np.clip(0.35 * condition_part + 0.25 * rms_part + 0.2 * arc_part + 0.2 * obs_part, 0, 1)
    )


def perturb_elements(
    elements: dict[str, float],
    n_clones: int,
    rng: np.random.Generator,
) -> dict[str, np.ndarray]:
    """Generate perturbed element arrays for orbital clones."""
    score = uncertainty_score(elements)
    scale = 0.5 + 4.0 * score
    a = max(float(elements["a"]), 0.05)
    e = float(elements["e"])
    n = max(float(elements["n"]), 1e-6)
    clones = {
        "a": rng.normal(a, max(0.0005, a * 0.0025 * scale), n_clones),
        "e": rng.normal(e, 0.0015 * scale, n_clones),
        "i": rng.normal(float(elements["i"]), 0.04 * scale, n_clones),
        "om": rng.normal(float(elements["om"]), 0.06 * scale, n_clones),
        "w": rng.normal(float(elements["w"]), 0.06 * scale, n_clones),
        "ma": rng.normal(float(elements["ma"]), 0.08 * scale, n_clones),
        "n": rng.normal(n, max(1e-6, n * 0.0015 * scale), n_clones),
    }
    clones["a"] = np.clip(clones["a"], 0.05, 12.0)
    clones["e"] = np.clip(clones["e"], 0.0, 0.98)
    clones["n"] = np.clip(clones["n"], 1e-6, None)
    return clones


def _safe_float(value: Any, default: float) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    if np.isnan(result):
        return default
    return result
