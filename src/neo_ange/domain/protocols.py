"""Structural domain contracts for Neo Angele objects and services."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class SerializableDomainObject(Protocol):
    """Object that can expose a nested domain representation."""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        ...


@runtime_checkable
class FeatureExportable(Protocol):
    """Object that can export model-ready flattened features."""

    def to_feature_dict(self) -> dict[str, Any]:
        """Return a model-friendly feature dictionary."""
        ...


@runtime_checkable
class IdentifiableDomainObject(Protocol):
    """Object with a stable key and a human-readable name."""

    def object_key(self) -> str:
        """Return the stable lookup key."""
        ...

    def display_name(self) -> str:
        """Return the display label."""
        ...


@runtime_checkable
class Summarizable(Protocol):
    """Object that can derive a summary view from detailed state."""

    def summarize(self) -> Any:
        """Return a summary value derived from this object."""
        ...


@runtime_checkable
class RiskScoringStrategy(Protocol):
    """Scoring service contract used by pipelines and simulations."""

    def score_row(self, row: Any) -> Any:
        """Score one analytical row."""
        ...

    def score_dataframe(self, df: Any) -> Any:
        """Score a dataframe of analytical rows."""
        ...


@runtime_checkable
class SimulationStrategy(Protocol):
    """Simulation service contract for object-level simulation engines."""

    def simulate_object(self, *args: Any, **kwargs: Any) -> Any:
        """Run one object-level simulation."""
        ...
