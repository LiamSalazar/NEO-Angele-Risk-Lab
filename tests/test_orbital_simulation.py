from __future__ import annotations

import pandas as pd

from neo_ange.orbital_simulation.monte_carlo import OrbitalMonteCarloEngine
from neo_ange.orbital_simulation.service import OrbitalSimulationService


def _orbital_row() -> dict[str, object]:
    return {
        "object_key": "A-001",
        "des": "2026 QA",
        "a": 1.12,
        "e": 0.18,
        "i": 4.2,
        "om": 80.0,
        "w": 22.0,
        "ma": 18.0,
        "moid": 0.025,
        "condition_code": 4,
        "rms": 0.4,
        "arc_length": 120,
        "n_obs_used": 35,
        "risk_score_0_100": 48.5,
        "risk_category": "elevated",
    }


def test_orbital_monte_carlo_generates_distance_trace() -> None:
    result = OrbitalMonteCarloEngine().simulate_object(
        _orbital_row(),
        n_clones=12,
        horizon_days=120,
        time_step_days=30,
        random_state=7,
    )

    assert result["object_key"] == "A-001"
    assert result["n_clones"] == 12
    assert result["simulated_min_distance_p05_au"] <= result["simulated_min_distance_p95_au"]
    assert result["scenario_category"] in {"stable", "variable", "uncertain", "needs_review"}
    assert result["distance_trace"]["day"]


def test_orbital_service_batch_excludes_trace_from_results(tmp_path) -> None:
    risk_dir = tmp_path / "gold" / "risk_scores"
    risk_dir.mkdir(parents=True)
    pd.DataFrame([_orbital_row()]).to_parquet(risk_dir / "risk_scores.parquet", index=False)

    service = OrbitalSimulationService(
        gold_root=tmp_path / "gold",
        report_dir=tmp_path / "reports" / "orbital_simulation",
        manifest_dir=tmp_path / "reports" / "manifests",
    )

    payload = service.simulate_batch(
        limit=1,
        n_clones=8,
        horizon_days=90,
        time_step_days=30,
        random_state=11,
    )

    assert payload["status"] == "success"
    assert len(payload["results"]) == 1
    assert "distance_trace" not in payload["results"][0]
    assert service.results_path.exists()
