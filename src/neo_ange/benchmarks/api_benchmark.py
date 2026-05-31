"""API benchmark helpers."""

from __future__ import annotations

import time
from typing import Any

from fastapi.testclient import TestClient

from neo_ange.api.main import app


def build_api_latency_benchmark() -> dict[str, Any]:
    """Measure basic API latency with FastAPI TestClient."""
    client = TestClient(app)
    endpoints = [
        "/health",
        "/status",
        "/rankings/summary",
        "/gnn/status",
        "/orbital-simulation/status",
    ]
    rows = []
    for endpoint in endpoints:
        started = time.perf_counter()
        response = client.get(endpoint)
        elapsed_ms = (time.perf_counter() - started) * 1000
        rows.append(
            {
                "endpoint": endpoint,
                "status_code": response.status_code,
                "elapsed_ms": elapsed_ms,
            }
        )
    return {"status": "success", "latency_rows": rows}
