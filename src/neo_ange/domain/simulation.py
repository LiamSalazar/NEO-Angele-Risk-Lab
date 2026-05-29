"""Simulation domain entities."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class SimulationScenario:
    """One perturbed score scenario from Monte Carlo simulation."""

    object_key: str
    simulation_id: str
    perturbed_values: dict[str, Any] = field(default_factory=dict)
    risk_score_0_100: float | None = None
    risk_category: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return asdict(self)


@dataclass(slots=True)
class MonteCarloResult:
    """Aggregated Monte Carlo score-stability result."""

    object_key: str
    n_simulations: int | None = None
    base_score: float | None = None
    mean_score: float | None = None
    std_score: float | None = None
    p05_score: float | None = None
    p25_score: float | None = None
    median_score: float | None = None
    p75_score: float | None = None
    p95_score: float | None = None
    max_score: float | None = None
    probability_score_above_60: float | None = None
    probability_score_above_80: float | None = None
    category_shift_probability: float | None = None
    base_category: str | None = None
    p95_category: str | None = None
    simulation_version: str | None = None

    def stability_summary(self) -> dict[str, Any]:
        """Return a compact interpretation of score stability."""
        shift_probability = self.category_shift_probability
        std_score = self.std_score
        if shift_probability is None and std_score is None:
            stability = "unknown"
        elif (shift_probability or 0.0) >= 0.35 or (std_score or 0.0) >= 15.0:
            stability = "unstable"
        elif (shift_probability or 0.0) >= 0.10 or (std_score or 0.0) >= 7.5:
            stability = "moderate"
        else:
            stability = "stable"
        return {
            "object_key": self.object_key,
            "stability": stability,
            "base_score": self.base_score,
            "mean_score": self.mean_score,
            "p95_score": self.p95_score,
            "base_category": self.base_category,
            "p95_category": self.p95_category,
            "category_shift_probability": shift_probability,
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return asdict(self)
