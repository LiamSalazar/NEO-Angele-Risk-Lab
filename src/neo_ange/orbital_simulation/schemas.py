"""Schemas and constants for approximate orbital simulation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

ORBITAL_SIMULATION_VERSION = "orbital-simulation-v0.1.0"


@dataclass(slots=True)
class OrbitalSimulationResult:
    """Summary for one object's approximate orbital perturbation run."""

    object_key: str
    n_clones: int
    horizon_days: int
    time_step_days: int
    baseline_min_distance_au: float | None
    simulated_min_distance_mean_au: float | None
    simulated_min_distance_p05_au: float | None
    simulated_min_distance_p50_au: float | None
    simulated_min_distance_p95_au: float | None
    closest_approach_day_mean: float | None
    closest_approach_day_p05: float | None
    closest_approach_day_p95: float | None
    dispersion_index: float | None
    orbital_uncertainty_score: float
    scenario_category: str
    interpretation: str
    warnings: list[str] = field(default_factory=list)
    simulated_at_utc: str | None = None
    simulation_version: str = ORBITAL_SIMULATION_VERSION
    designation: str | None = None
    risk_score_0_100: float | None = None
    risk_category: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly dictionary."""
        return asdict(self)
