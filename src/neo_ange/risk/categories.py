"""Experimental risk-priority category assignment."""

from __future__ import annotations

import math
from typing import Any


class RiskCategoryAssigner:
    """Map 0-100 experimental risk-priority scores into readable bands."""

    _CATEGORIES: dict[str, dict[str, Any]] = {
        "low": {
            "min": 0.0,
            "max": 20.0,
            "description": (
                "Low experimental follow-up priority in this educational scoring system. "
                "This is not an official alert."
            ),
        },
        "moderate": {
            "min": 20.0,
            "max": 40.0,
            "description": (
                "Moderate experimental follow-up priority based on the available features. "
                "This is not an official alert."
            ),
        },
        "elevated": {
            "min": 40.0,
            "max": 60.0,
            "description": (
                "Elevated experimental follow-up priority; component drivers should be "
                "reviewed with the data limitations in mind. This is not an official alert."
            ),
        },
        "high": {
            "min": 60.0,
            "max": 80.0,
            "description": (
                "High experimental follow-up priority for this lab score. It does not replace "
                "NASA/JPL CNEOS, Sentry, or any official risk assessment."
            ),
        },
        "critical": {
            "min": 80.0,
            "max": 100.0,
            "description": (
                "Critical experimental follow-up priority in this prototype ranking. Treat it "
                "as an analytical flag, not an official warning or impact prediction."
            ),
        },
    }

    def assign(self, score_0_100: float) -> str:
        """Return a category for a 0-100 score, clipping invalid extremes."""
        score = _clean_score(score_0_100)
        if score < 20.0:
            return "low"
        if score < 40.0:
            return "moderate"
        if score < 60.0:
            return "elevated"
        if score < 80.0:
            return "high"
        return "critical"

    def describe(self, category: str) -> str:
        """Describe a category with the experimental-score disclaimer included."""
        normalized = str(category).strip().lower()
        if normalized not in self._CATEGORIES:
            return (
                "Unknown experimental priority category. This lab score is not an official "
                "alert or impact prediction."
            )
        return str(self._CATEGORIES[normalized]["description"])

    def all_categories(self) -> dict[str, dict[str, Any]]:
        """Return the configured category bands and descriptions."""
        return {key: dict(value) for key, value in self._CATEGORIES.items()}


def _clean_score(value: float) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(score):
        return 0.0
    return min(max(score, 0.0), 100.0)
