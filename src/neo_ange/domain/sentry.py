"""Sentry risk-signal domain entity."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass


@dataclass(slots=True)
class SentryRiskSignal:
    """Fields related to CNEOS Sentry impact-monitoring records."""

    sentry_flag: bool | None = None
    sentry_ip: float | None = None
    sentry_ps_cum: float | None = None
    sentry_ps_max: float | None = None
    sentry_ts_max: float | None = None
    sentry_n_imp: int | None = None

    def has_sentry_signal(self) -> bool:
        """Return whether there is any explicit Sentry signal in the row."""
        if self.sentry_flag is True:
            return True
        return any(
            _to_float(value) is not None
            for value in (
                self.sentry_ip,
                self.sentry_ps_cum,
                self.sentry_ps_max,
                self.sentry_ts_max,
                self.sentry_n_imp,
            )
        )

    def sentry_priority_indicator(self) -> float | None:
        """Return a bounded signal from impact probability and Sentry scales."""
        signals: list[float] = []
        if self.sentry_flag is not None:
            signals.append(1.0 if self.sentry_flag else 0.0)
        ip = _to_float(self.sentry_ip)
        if ip is not None:
            signals.append(_probability_signal(ip))
        ps_cum = _to_float(self.sentry_ps_cum)
        if ps_cum is not None:
            signals.append(_palermo_signal(ps_cum))
        ps_max = _to_float(self.sentry_ps_max)
        if ps_max is not None:
            signals.append(_palermo_signal(ps_max))
        ts_max = _to_float(self.sentry_ts_max)
        if ts_max is not None:
            signals.append(_bounded(ts_max / 10.0))
        n_imp = _to_float(self.sentry_n_imp)
        if n_imp is not None:
            signals.append(_bounded(math.log1p(max(n_imp, 0.0)) / math.log1p(100.0)))
        if not signals:
            return None
        return _bounded(sum(signals) / len(signals))

    def to_dict(self) -> dict[str, bool | float | int | None]:
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


def _probability_signal(value: float) -> float:
    probability = _bounded(value, 0.0, 1.0)
    if probability <= 0:
        return 0.0
    return _bounded((math.log10(probability) + 10.0) / 10.0)


def _palermo_signal(value: float) -> float:
    return _bounded((value + 8.0) / 10.0)
