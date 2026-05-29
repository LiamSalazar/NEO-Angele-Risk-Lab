"""Orbital domain entities."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass


@dataclass(slots=True)
class Orbit:
    """Classical orbital elements and observation-quality metadata."""

    e: float | None = None
    a: float | None = None
    q: float | None = None
    i: float | None = None
    om: float | None = None
    w: float | None = None
    ma: float | None = None
    n: float | None = None
    per: float | None = None
    ad: float | None = None
    moid: float | None = None
    moid_ld: float | None = None
    condition_code: str | float | int | None = None
    arc_length: float | None = None
    n_obs_used: int | None = None
    rms: float | None = None

    def has_minimum_orbital_data(self) -> bool:
        """Return whether the row has enough elements to compare orbital geometry."""
        return all(_is_number(value) for value in (self.e, self.a, self.q, self.i))

    def orbital_vector(self) -> list[float]:
        """Return a fixed-width numeric vector for graph and model features."""
        return [
            _zero_if_missing(value)
            for value in (
                self.e,
                self.a,
                self.q,
                self.i,
                self.om,
                self.w,
                self.ma,
                self.n,
                self.per,
                self.ad,
                self.moid,
                self.moid_ld,
            )
        ]

    def proximity_indicator(self) -> float | None:
        """Return a bounded inverse-distance signal based on MOID when available."""
        moid = _to_float(self.moid)
        if moid is not None and moid >= 0:
            return _bounded(1.0 / (1.0 + moid * 20.0))
        moid_ld = _to_float(self.moid_ld)
        if moid_ld is not None and moid_ld >= 0:
            return _bounded(1.0 / (1.0 + moid_ld / 10.0))
        return None

    def uncertainty_indicator(self) -> float | None:
        """Return a bounded follow-up uncertainty proxy from orbit-quality fields."""
        signals: list[float] = []
        condition = _to_float(self.condition_code)
        if condition is not None:
            signals.append(_bounded(condition / 9.0))
        rms = _to_float(self.rms)
        if rms is not None:
            signals.append(_bounded(rms / 2.0))
        arc = _to_float(self.arc_length)
        if arc is not None:
            signals.append(1.0 - _bounded(math.log1p(max(arc, 0.0)) / math.log1p(3650.0)))
        n_obs = _to_float(self.n_obs_used)
        if n_obs is not None:
            signals.append(1.0 - _bounded(math.log1p(max(n_obs, 0.0)) / math.log1p(1000.0)))
        if not signals:
            return None
        return _bounded(sum(signals) / len(signals))

    def to_dict(self) -> dict[str, float | int | str | None]:
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


def _is_number(value: object) -> bool:
    return _to_float(value) is not None


def _zero_if_missing(value: object) -> float:
    numeric = _to_float(value)
    return 0.0 if numeric is None else float(numeric)


def _bounded(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    if not math.isfinite(value):
        return lower
    return min(max(float(value), lower), upper)
