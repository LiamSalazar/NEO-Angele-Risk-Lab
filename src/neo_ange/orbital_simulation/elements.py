"""Orbital element extraction helpers."""

from __future__ import annotations

from typing import Any

import pandas as pd

REQUIRED_ORBITAL_COLUMNS = ["a", "e", "i", "om", "w", "ma"]


def extract_elements(row: dict[str, Any] | pd.Series) -> tuple[dict[str, float], list[str]]:
    """Extract numeric orbital elements with warnings for missing values."""
    if isinstance(row, pd.Series):
        source = row.to_dict()
    else:
        source = row
    warnings: list[str] = []
    elements: dict[str, float] = {}
    for column in [
        "a",
        "e",
        "i",
        "om",
        "w",
        "ma",
        "n",
        "per",
        "moid",
        "condition_code",
        "rms",
        "arc_length",
        "n_obs_used",
    ]:
        elements[column] = _to_float(source.get(column))
    if elements["a"] is None or elements["a"] <= 0:
        warnings.append("Semi-major axis is missing; defaulting to 1 AU for propagation.")
        elements["a"] = 1.0
    if elements["e"] is None:
        warnings.append("Eccentricity is missing; defaulting to 0 for propagation.")
        elements["e"] = 0.0
    elements["e"] = max(0.0, min(0.98, float(elements["e"])))
    for angle in ["i", "om", "w", "ma"]:
        if elements[angle] is None:
            warnings.append(f"{angle} is missing; defaulting to 0 degrees.")
            elements[angle] = 0.0
    if elements["n"] is None or elements["n"] <= 0:
        period = elements.get("per")
        if period and period > 0:
            elements["n"] = 360.0 / period
        else:
            elements["n"] = 0.9856076686 / (float(elements["a"]) ** 1.5)
            warnings.append("Mean motion is missing; approximated from semi-major axis.")
    return elements, warnings


def _to_float(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(result):
        return None
    return result
