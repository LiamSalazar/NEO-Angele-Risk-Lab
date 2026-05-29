"""Close-approach domain entities."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass


@dataclass(slots=True)
class CloseApproach:
    """One recorded close approach to a planetary body."""

    close_approach_datetime: str | None = None
    dist: float | None = None
    dist_min: float | None = None
    dist_max: float | None = None
    v_rel: float | None = None
    v_inf: float | None = None
    body: str | None = None

    def distance_indicator(self) -> float | None:
        """Return an inverse-distance signal from the closest available distance."""
        distance = _first_number(self.dist_min, self.dist, self.dist_max)
        if distance is None or distance < 0:
            return None
        return _bounded(1.0 / (1.0 + distance * 25.0))

    def velocity_indicator(self) -> float | None:
        """Return a bounded velocity signal from relative or asymptotic speed."""
        velocity = _first_number(self.v_rel, self.v_inf)
        if velocity is None:
            return None
        return _bounded(velocity / 50.0)

    def to_dict(self) -> dict[str, float | str | None]:
        """Serialize to a plain dictionary."""
        return asdict(self)


@dataclass(slots=True)
class CloseApproachSummary:
    """Aggregated close-approach context for one object."""

    min_close_approach_dist: float | None = None
    min_close_approach_dist_min: float | None = None
    max_close_approach_v_rel: float | None = None
    next_close_approach_datetime: str | None = None
    close_approach_count: int | None = None

    def has_close_approach_data(self) -> bool:
        """Return whether any close-approach aggregate is present."""
        return any(
            value is not None
            for value in (
                self.min_close_approach_dist,
                self.min_close_approach_dist_min,
                self.max_close_approach_v_rel,
                self.next_close_approach_datetime,
                self.close_approach_count,
            )
        )

    def approach_priority_indicator(self) -> float | None:
        """Return a bounded priority signal from distance, velocity, and count."""
        signals: list[float] = []
        distance = _first_number(self.min_close_approach_dist_min, self.min_close_approach_dist)
        if distance is not None and distance >= 0:
            signals.append(_bounded(1.0 / (1.0 + distance * 25.0)))
        velocity = _to_float(self.max_close_approach_v_rel)
        if velocity is not None:
            signals.append(_bounded(velocity / 50.0))
        count = _to_float(self.close_approach_count)
        if count is not None:
            signals.append(_bounded(math.log1p(max(count, 0.0)) / math.log1p(25.0)))
        if not signals:
            return None
        return _bounded(sum(signals) / len(signals))

    def to_dict(self) -> dict[str, float | int | str | None]:
        """Serialize to a plain dictionary."""
        return asdict(self)


def _first_number(*values: object) -> float | None:
    for value in values:
        numeric = _to_float(value)
        if numeric is not None:
            return numeric
    return None


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numeric):
        return None
    return numeric


def _bounded(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    if not math.isfinite(value):
        return lower
    return min(max(float(value), lower), upper)
