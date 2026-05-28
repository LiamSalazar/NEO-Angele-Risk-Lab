from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from neo_ange.spark.session import create_spark_session, stop_spark_session


@pytest.fixture(scope="session")
def spark():
    session = create_spark_session(
        app_name="neo-ange-risk-lab-test",
        master="local[2]",
        log_level="ERROR",
    )
    yield session
    stop_spark_session(session)


@pytest.fixture
def write_bronze(
    tmp_path,
) -> Callable[[str, dict[str, Any], dict[str, Any] | None, str | None], Path]:
    def writer(
        source: str,
        payload: dict[str, Any],
        query_params: dict[str, Any] | None = None,
        object_id: str | None = None,
    ) -> Path:
        output_dir = tmp_path / "bronze" / source / "ingest_date=2026-05-28"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{object_id or 'sample'}.json"
        wrapper = {
            "metadata": {
                "source": source,
                "ingested_at_utc": "2026-05-28T00:00:00+00:00",
                "query_params": query_params or {},
                "object_id": object_id,
                "api_signature": payload.get("signature", {"version": "test"}),
            },
            "data": payload,
        }
        output_path.write_text(json.dumps(wrapper), encoding="utf-8")
        return output_path

    return writer
