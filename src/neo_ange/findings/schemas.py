"""Schemas for user-facing analytical findings."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class AnalyticalFinding:
    """One interpretable conclusion backed by project artifacts."""

    title: str
    short_text: str
    technical_basis: str
    related_objects: list[str] = field(default_factory=list)
    importance: str = "medium"
    source_module: str = "dataset"
    values: dict[str, Any] = field(default_factory=dict)
    caveat: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly dictionary."""
        return asdict(self)


def finding(
    title: str,
    short_text: str,
    technical_basis: str,
    *,
    related_objects: list[str] | None = None,
    importance: str = "medium",
    source_module: str = "dataset",
    values: dict[str, Any] | None = None,
    caveat: str | None = None,
) -> dict[str, Any]:
    """Build a JSON-friendly finding without exposing dataclass details to callers."""
    return AnalyticalFinding(
        title=title,
        short_text=short_text,
        technical_basis=technical_basis,
        related_objects=related_objects or [],
        importance=importance,
        source_module=source_module,
        values=values or {},
        caveat=caveat,
    ).to_dict()
