"""Experiment orchestration for orbital graph learning."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from neo_ange.gnn.baselines import GraphBaselineRunner
from neo_ange.gnn.datasets import GNNDatasetBuilder, torch_geometric_available
from neo_ange.gnn.graph_builder import OrbitalGraphBuilder
from neo_ange.gnn.reporting import GNNReportWriter
from neo_ange.gnn.schemas import GNN_EXPERIMENT_VERSION
from neo_ange.gnn.training import GNNTrainer
from neo_ange.manifests.run_manifest import (
    RunManifest,
    create_run_id,
    save_manifest,
    utc_now_manifest,
)
from neo_ange.utils.serialization import to_jsonable, write_json


class GNNExperimentRunner:
    """Run graph construction, baselines, optional GNN training, and reports."""

    def __init__(
        self,
        gold_root: str | Path = "data/gold",
        graph_output_dir: str | Path = "data/gold/gnn_graph",
        report_dir: str | Path = "reports/gnn",
        manifest_dir: str | Path = "reports/manifests",
    ) -> None:
        self.gold_root = Path(gold_root)
        self.graph_output_dir = Path(graph_output_dir)
        self.report_dir = Path(report_dir)
        self.manifest_dir = Path(manifest_dir)
        self.graph_builder = OrbitalGraphBuilder(gold_root=self.gold_root, report_dir=report_dir)
        self.dataset_builder = GNNDatasetBuilder()
        self.baselines = GraphBaselineRunner()
        self.trainer = GNNTrainer()
        self.report_writer = GNNReportWriter(report_dir=report_dir)

    def run_graph_experiment(
        self,
        target: str = "pha",
        k: int = 10,
        min_nodes: int = 100,
    ) -> dict[str, Any]:
        """Build and export an orbital graph."""
        graph = self.graph_builder.build_graph_from_risk_scores(
            k=k,
            target=target,
            min_nodes=min_nodes,
        )
        outputs = self.graph_builder.export_graph(graph, output_dir=self.graph_output_dir)
        summary = outputs["graph_summary"]
        status = summary.get("status", "success")
        return to_jsonable(
            {
                "status": status,
                "target": target,
                "k": k,
                "min_nodes": min_nodes,
                "n_nodes": graph.node_count(),
                "n_edges": graph.edge_count(),
                "graph_summary": summary,
                "outputs": outputs,
                "warnings": summary.get("warnings", []),
            }
        )

    def run_baseline_comparison(
        self,
        df: pd.DataFrame | None = None,
        target: str = "pha",
    ) -> dict[str, Any]:
        """Run tabular baselines against graph-node feature sets."""
        source_df = df if df is not None else self.graph_builder._load_source_dataframe()
        return self.baselines.run_all(source_df, target=target)

    def run_all(
        self,
        target: str = "pha",
        k: int = 10,
        min_nodes: int = 100,
    ) -> dict[str, Any]:
        """Run the full graph research workflow and persist reports/manifests."""
        run_id = create_run_id("gnn")
        started_at = utc_now_manifest()
        warnings: list[str] = []
        graph_result = self.run_graph_experiment(target=target, k=k, min_nodes=min_nodes)
        source_df = self.graph_builder._load_source_dataframe()
        baseline_metrics = self.run_baseline_comparison(source_df, target=target)
        gnn_metrics: dict[str, Any] = {}

        status = graph_result["status"]
        if status == "insufficient_data":
            warnings.extend(graph_result.get("warnings", []))
        else:
            graph = self.graph_builder.build_graph_from_risk_scores(
                k=k,
                target=target,
                min_nodes=1,
            )
            dataset = self.dataset_builder.to_torch_geometric_data(graph, target=target)
            if not torch_geometric_available():
                gnn_metrics = {
                    "graphsage": {
                        "status": "skipped_missing_dependency",
                        "metrics": {},
                        "warnings": ["torch-geometric is not installed."],
                    },
                    "gcn": {
                        "status": "skipped_missing_dependency",
                        "metrics": {},
                        "warnings": ["torch-geometric is not installed."],
                    },
                }
                warnings.append("torch-geometric is not installed; real GNN training was skipped.")
                status = "partial_success"
            else:
                gnn_metrics = {
                    "graphsage": self.trainer.train_graphsage(dataset),
                    "gcn": self.trainer.train_gcn(dataset),
                }
                if any(payload.get("status") != "success" for payload in gnn_metrics.values()):
                    status = "partial_success"

        result = {
            "status": status,
            "experiment_id": run_id,
            "experiment_version": GNN_EXPERIMENT_VERSION,
            "target": target,
            "k": k,
            "min_nodes": min_nodes,
            "n_nodes": graph_result.get("n_nodes", 0),
            "n_edges": graph_result.get("n_edges", 0),
            "graph_summary": graph_result.get("graph_summary", {}),
            "baseline_metrics": baseline_metrics,
            "gnn_metrics": gnn_metrics,
            "warnings": warnings,
            "artifacts": graph_result.get("outputs", {}),
        }
        report_outputs = self.report_writer.write_outputs(result)
        manifest_path = self._save_manifest(run_id, started_at, result, report_outputs)
        result["artifacts"] = {
            **result["artifacts"],
            **report_outputs,
            "manifest": str(manifest_path),
        }
        write_json(result, self.report_dir / "gnn_experiment_results.json")
        return to_jsonable(result)

    def _save_manifest(
        self,
        run_id: str,
        started_at: str,
        result: dict[str, Any],
        report_outputs: dict[str, str],
    ) -> Path:
        manifest = RunManifest(
            run_id=run_id,
            run_type="gnn",
            started_at_utc=started_at,
            ended_at_utc=utc_now_manifest(),
            status=result["status"],
            inputs={"target": result["target"], "k": result["k"], "min_nodes": result["min_nodes"]},
            outputs={**result.get("artifacts", {}), **report_outputs},
            metrics={
                "n_nodes": result.get("n_nodes", 0),
                "n_edges": result.get("n_edges", 0),
                "torch_geometric_available": torch_geometric_available(),
            },
            warnings=result.get("warnings", []),
            errors=[],
        )
        return save_manifest(manifest, output_dir=self.manifest_dir)
