"""FastAPI dependency factories."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from neo_ange.gnn.experiments import GNNExperimentRunner
from neo_ange.pipelines.risk import RiskPipeline
from neo_ange.pipelines.simulation import SimulationPipeline
from neo_ange.utils.config import get_settings


def get_data_paths() -> dict[str, Path]:
    """Return configured data and report paths without loading datasets."""
    settings = get_settings()
    data_dir = Path(settings.data_dir)
    gold_dir = Path(settings.gold_dir)
    silver_dir = Path(settings.silver_dir)
    return {
        "data_dir": data_dir,
        "bronze_dir": data_dir / "bronze",
        "silver_dir": silver_dir,
        "gold_dir": gold_dir,
        "gold_features_dir": gold_dir / "neo_risk_features",
        "risk_scores_dir": gold_dir / "risk_scores",
        "simulation_results_dir": gold_dir / "simulation_results",
        "gnn_graph_dir": gold_dir / "gnn_graph",
        "reports_dir": Path("reports"),
        "manifest_dir": Path("reports/manifests"),
    }


def get_risk_pipeline() -> RiskPipeline:
    """Build a risk pipeline on demand."""
    paths = get_data_paths()
    return RiskPipeline(
        gold_root=paths["gold_dir"],
        risk_output_dir=paths["risk_scores_dir"],
        report_dir=paths["reports_dir"] / "risk",
        manifest_dir=paths["manifest_dir"],
    )


def get_simulation_pipeline() -> SimulationPipeline:
    """Build a simulation pipeline on demand."""
    paths = get_data_paths()
    return SimulationPipeline(
        gold_root=paths["gold_dir"],
        risk_scores_dir=paths["risk_scores_dir"],
        simulation_output_dir=paths["simulation_results_dir"],
        report_dir=paths["reports_dir"] / "simulation",
        manifest_dir=paths["manifest_dir"],
    )


def get_gnn_runner() -> GNNExperimentRunner:
    """Build a GNN experiment runner on demand."""
    paths = get_data_paths()
    return GNNExperimentRunner(
        gold_root=paths["gold_dir"],
        graph_output_dir=paths["gnn_graph_dir"],
        report_dir=paths["reports_dir"] / "gnn",
        manifest_dir=paths["manifest_dir"],
    )


def serialize_paths(paths: dict[str, Path]) -> dict[str, Any]:
    """Convert dependency paths into JSON-friendly strings."""
    return {key: str(value) for key, value in paths.items()}
