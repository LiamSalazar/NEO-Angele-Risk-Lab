"""Close-approach domain entities."""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime


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


@dataclass(frozen=True, slots=True)
class CloseApproachHistory:
    """Collection of normalized CAD close approaches for one asteroid."""

    approaches: tuple[CloseApproach, ...] = ()

    def count(self) -> int:
        """Return the number of close-approach records in this history."""
        return len(self.approaches)

    def has_approaches(self) -> bool:
        """Return whether the history contains at least one approach."""
        return bool(self.approaches)

    def closest(self) -> CloseApproach | None:
        """Return the approach with the smallest available distance."""
        return _min_by_number(
            self.approaches,
            lambda approach: _first_number(approach.dist_min, approach.dist, approach.dist_max),
        )

    def fastest(self) -> CloseApproach | None:
        """Return the approach with the greatest available velocity."""
        return _max_by_number(
            self.approaches,
            lambda approach: _first_number(approach.v_rel, approach.v_inf),
        )

    def next_approach(self) -> CloseApproach | None:
        """Return the earliest approach with a comparable date."""
        dated = [
            (parsed, index, approach)
            for index, approach in enumerate(self.approaches)
            if (parsed := _parse_datetime(approach.close_approach_datetime)) is not None
        ]
        if dated:
            return min(dated, key=lambda item: (item[0], item[1]))[2]
        for approach in self.approaches:
            if approach.close_approach_datetime:
                return approach
        return None

    def summarize(self) -> CloseApproachSummary:
        """Build the aggregate summary used by scoring, API responses, and reports."""
        closest = self.closest()
        fastest = self.fastest()
        next_approach = self.next_approach()
        return CloseApproachSummary(
            min_close_approach_dist=(
                _first_number(closest.dist, closest.dist_min, closest.dist_max)
                if closest is not None
                else None
            ),
            min_close_approach_dist_min=(
                _first_number(closest.dist_min, closest.dist, closest.dist_max)
                if closest is not None
                else None
            ),
            max_close_approach_v_rel=(
                _first_number(fastest.v_rel, fastest.v_inf) if fastest is not None else None
            ),
            next_close_approach_datetime=(
                next_approach.close_approach_datetime if next_approach is not None else None
            ),
            close_approach_count=self.count() if self.has_approaches() else None,
        )

    def to_dict(self) -> dict[str, list[dict[str, float | str | None]] | int]:
        """Serialize this history without flattening individual approaches."""
        return {
            "approaches": [approach.to_dict() for approach in self.approaches],
            "close_approach_count": self.count(),
        }


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


def _min_by_number(
    approaches: tuple[CloseApproach, ...], selector: Callable[[CloseApproach], float | None]
) -> CloseApproach | None:
    numeric = [
        (value, index, approach)
        for index, approach in enumerate(approaches)
        if (value := selector(approach)) is not None
    ]
    if not numeric:
        return None
    return min(numeric, key=lambda item: (item[0], item[1]))[2]


def _max_by_number(
    approaches: tuple[CloseApproach, ...], selector: Callable[[CloseApproach], float | None]
) -> CloseApproach | None:
    numeric = [
        (value, index, approach)
        for index, approach in enumerate(approaches)
        if (value := selector(approach)) is not None
    ]
    if not numeric:
        return None
    return max(numeric, key=lambda item: (item[0], -item[1]))[2]


def _parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
        return parsed.replace(tzinfo=None)
    except ValueError:
        pass
    for date_format in ("%Y-%b-%d %H:%M", "%Y-%b-%d", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, date_format)
        except ValueError:
            continue
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
