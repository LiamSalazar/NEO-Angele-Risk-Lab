"""Physical asteroid properties."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass


@dataclass(slots=True)
class PhysicalProperties:
    """Physical properties and size proxies for one object."""

    h: float | None = None
    diameter: float | None = None
    albedo: float | None = None
    log_diameter: float | None = None

    def size_indicator(self) -> float | None:
        """Return a bounded size signal from diameter, log diameter, or H magnitude."""
        diameter = _to_float(self.diameter)
        if diameter is not None and diameter > 0:
            return _bounded(math.log1p(diameter) / math.log1p(10.0))
        log_diameter = _to_float(self.log_diameter)
        if log_diameter is not None and log_diameter > 0:
            return _bounded(log_diameter / math.log1p(10.0))
        h_value = _to_float(self.h)
        if h_value is not None:
            return _bounded((30.0 - h_value) / 15.0)
        return None

    def has_size_information(self) -> bool:
        """Return whether any size-related measurement or proxy is available."""
        return any(_to_float(value) is not None for value in (self.h, self.diameter, self.albedo))

    def to_dict(self) -> dict[str, float | None]:
        """Serialize to a plain dictionary."""
        return asdict(self)


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
