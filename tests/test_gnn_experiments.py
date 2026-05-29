from __future__ import annotations

import pandas as pd

from neo_ange.gnn.experiments import GNNExperimentRunner


def test_gnn_experiment_generates_insufficient_data_reports(tmp_path) -> None:
    risk_dir = tmp_path / "gold" / "risk_scores"
    risk_dir.mkdir(parents=True)
    pd.DataFrame(
        {
            "object_key": ["a", "b"],
            "pha": [True, False],
            "e": [0.1, 0.2],
            "a": [1.0, 1.1],
            "q": [0.8, 0.9],
            "i": [2.0, 3.0],
        }
    ).to_parquet(risk_dir / "risk_scores.parquet")

    runner = GNNExperimentRunner(
        gold_root=tmp_path / "gold",
        graph_output_dir=tmp_path / "gold" / "gnn_graph",
        report_dir=tmp_path / "reports" / "gnn",
        manifest_dir=tmp_path / "reports" / "manifests",
    )
    result = runner.run_all(min_nodes=10)

    assert result["status"] == "insufficient_data"
    assert (tmp_path / "reports" / "gnn" / "gnn_summary.md").exists()
    assert list((tmp_path / "reports" / "manifests").glob("gnn_*.json"))
