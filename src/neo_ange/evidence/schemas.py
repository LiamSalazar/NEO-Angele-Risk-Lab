"""Lightweight schemas for model evidence artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ModelCard:
    """Interpretive card for one model/feature-set evidence view."""

    model_name: str
    model_family: str
    feature_set: str
    target: str
    metrics: dict[str, Any]
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    leakage_risk: str = "medium"
    recommended_use: str = ""
    not_recommended_use: str = ""
    interpretation: str = ""
    status: str = "success"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly dictionary."""
        return asdict(self)


@dataclass(slots=True)
class PredictionRecord:
    """Observable object-level prediction emitted by an evidence model."""

    object_key: str
    designation: str | None
    actual_label: int
    predicted_label: int
    predicted_probability: float
    model_name: str
    feature_set: str
    model_family: str
    correct: bool
    confidence_bucket: str
    risk_score_0_100: float | None
    risk_category: str | None
    notes: str = ""
    graph_model_name: str | None = None
    node_embedding_dimension: int | None = None
    neighbor_context_used: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly dictionary."""
        return asdict(self)
