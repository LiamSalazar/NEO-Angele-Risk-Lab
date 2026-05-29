from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from neo_ange.api.dependencies import get_data_paths, get_gnn_runner
from neo_ange.api.main import app


def _paths(tmp_path) -> dict[str, Path]:
    return {
        "data_dir": tmp_path / "data",
        "bronze_dir": tmp_path / "data" / "bronze",
        "silver_dir": tmp_path / "data" / "silver",
        "gold_dir": tmp_path / "data" / "gold",
        "gold_features_dir": tmp_path / "data" / "gold" / "neo_risk_features",
        "risk_scores_dir": tmp_path / "data" / "gold" / "risk_scores",
        "simulation_results_dir": tmp_path / "data" / "gold" / "simulation_results",
        "gnn_graph_dir": tmp_path / "data" / "gold" / "gnn_graph",
        "reports_dir": tmp_path / "reports",
        "manifest_dir": tmp_path / "reports" / "manifests",
    }


def test_gnn_api_status_and_missing_neighbors(tmp_path) -> None:
    app.dependency_overrides[get_data_paths] = lambda: _paths(tmp_path)
    try:
        client = TestClient(app)
        status = client.get("/gnn/status")
        neighbors = client.get("/gnn/object/missing/neighbors")
    finally:
        app.dependency_overrides.clear()

    assert status.status_code == 200
    assert status.json()["status"] == "ok"
    assert neighbors.status_code == 200
    assert neighbors.json()["status"] == "missing_data"


def test_gnn_api_build_graph_uses_runner_override() -> None:
    class FakeRunner:
        def run_graph_experiment(self, k=10, min_nodes=100):
            return {"status": "insufficient_data", "k": k, "min_nodes": min_nodes}

    app.dependency_overrides[get_gnn_runner] = lambda: FakeRunner()
    try:
        response = TestClient(app).post("/gnn/build-graph", json={"k": 2, "min_nodes": 10})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "insufficient_data"


def test_gnn_api_summary_missing(tmp_path) -> None:
    app.dependency_overrides[get_data_paths] = lambda: _paths(tmp_path)
    try:
        response = TestClient(app).get("/gnn/summary")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "missing_data"
