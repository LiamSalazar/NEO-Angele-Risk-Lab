from __future__ import annotations

from fastapi.testclient import TestClient

from neo_ange.api.main import app


def test_health_returns_ok() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_status_returns_ok() -> None:
    response = TestClient(app).get("/status")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
