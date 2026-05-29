from __future__ import annotations

from fastapi.testclient import TestClient

from neo_ange.api.dependencies import get_simulation_pipeline
from neo_ange.api.main import app
from neo_ange.pipelines.simulation import SimulationPipeline


def test_simulation_status_responds(tmp_path) -> None:
    pipeline = SimulationPipeline(
        gold_root=tmp_path / "gold",
        report_dir=tmp_path / "reports" / "simulation",
        manifest_dir=tmp_path / "reports" / "manifests",
    )
    app.dependency_overrides[get_simulation_pipeline] = lambda: pipeline
    try:
        response = TestClient(app).get("/simulations/status")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_simulation_object_handles_missing_data(tmp_path) -> None:
    pipeline = SimulationPipeline(
        gold_root=tmp_path / "gold",
        report_dir=tmp_path / "reports" / "simulation",
        manifest_dir=tmp_path / "reports" / "manifests",
    )
    app.dependency_overrides[get_simulation_pipeline] = lambda: pipeline
    try:
        response = TestClient(app).post(
            "/simulations/object",
            json={"object_key": "A", "n_simulations": 10, "random_state": 42},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "failed"


def test_simulation_batch_handles_missing_data(tmp_path) -> None:
    pipeline = SimulationPipeline(
        gold_root=tmp_path / "gold",
        report_dir=tmp_path / "reports" / "simulation",
        manifest_dir=tmp_path / "reports" / "manifests",
    )
    app.dependency_overrides[get_simulation_pipeline] = lambda: pipeline
    try:
        response = TestClient(app).post(
            "/simulations/batch",
            json={"limit": 2, "n_simulations": 10, "random_state": 42},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "failed"
