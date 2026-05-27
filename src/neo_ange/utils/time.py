"""UTC time helpers for ingestion metadata and partitions."""

from __future__ import annotations

from datetime import UTC, datetime


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def utc_timestamp_compact() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")


def current_utc_date_partition() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")
