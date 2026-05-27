"""Lightweight domain models for ingestion metadata."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class APIRequestInfo(BaseModel):
    """Metadata about the source request used for a bronze record."""

    query_params: dict[str, Any] = Field(default_factory=dict)
    object_id: str | None = None
    api_signature: dict[str, Any] = Field(default_factory=dict)


class IngestionMetadata(APIRequestInfo):
    """Metadata attached to each raw bronze payload."""

    source: str
    ingested_at_utc: str


class BronzeRecord(BaseModel):
    """Raw source payload wrapped with ingestion metadata."""

    metadata: IngestionMetadata
    data: dict[str, Any]
