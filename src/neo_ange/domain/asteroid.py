"""Asteroid aggregate root."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from neo_ange.domain.approach import CloseApproachSummary
from neo_ange.domain.identity import AsteroidIdentity
from neo_ange.domain.orbit import Orbit
from neo_ange.domain.physical import PhysicalProperties
from neo_ange.domain.sentry import SentryRiskSignal


@dataclass(slots=True)
class Asteroid:
    """Domain aggregate containing risk-relevant asteroid state."""

    identity: AsteroidIdentity
    orbit: Orbit
    physical: PhysicalProperties
    close_approach_summary: CloseApproachSummary | None = None
    sentry_signal: SentryRiskSignal | None = None
    neo: bool | None = None
    pha: bool | None = None

    def object_key(self) -> str:
        """Return the stable lookup key used across layers."""
        return self.identity.best_identifier()

    def display_name(self) -> str:
        """Return a human-readable display label."""
        return self.identity.display_name()

    def has_risk_relevant_data(self) -> bool:
        """Return whether at least one risk-relevant domain area is populated."""
        return any(
            [
                self.orbit.has_minimum_orbital_data(),
                self.physical.has_size_information(),
                self.close_approach_summary is not None
                and self.close_approach_summary.has_close_approach_data(),
                self.sentry_signal is not None and self.sentry_signal.has_sentry_signal(),
                self.neo is not None,
                self.pha is not None,
            ]
        )

    def to_feature_dict(self) -> dict[str, Any]:
        """Return a flattened, model-friendly feature dictionary."""
        features: dict[str, Any] = {
            **self.identity.to_dict(),
            **self.orbit.to_dict(),
            **self.physical.to_dict(),
            "neo": self.neo,
            "pha": self.pha,
            "orbit_proximity_indicator": self.orbit.proximity_indicator(),
            "orbit_uncertainty_indicator": self.orbit.uncertainty_indicator(),
            "physical_size_indicator": self.physical.size_indicator(),
        }
        if self.close_approach_summary is not None:
            features.update(self.close_approach_summary.to_dict())
            features["approach_priority_indicator"] = (
                self.close_approach_summary.approach_priority_indicator()
            )
        if self.sentry_signal is not None:
            features.update(self.sentry_signal.to_dict())
            features["sentry_priority_indicator"] = self.sentry_signal.sentry_priority_indicator()
        return features

    def to_dict(self) -> dict[str, Any]:
        """Serialize the aggregate without flattening nested domain areas."""
        return {
            "identity": self.identity.to_dict(),
            "orbit": self.orbit.to_dict(),
            "physical": self.physical.to_dict(),
            "close_approach_summary": (
                self.close_approach_summary.to_dict()
                if self.close_approach_summary is not None
                else None
            ),
            "sentry_signal": (
                self.sentry_signal.to_dict() if self.sentry_signal is not None else None
            ),
            "neo": self.neo,
            "pha": self.pha,
        }
