"""GNN research-lab endpoints."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any

import pandas as pd
from fastapi import APIRouter, Depends

from neo_ange.api.dependencies import get_data_paths, get_gnn_runner
from neo_ange.api.schemas import GNNBuildGraphRequest, GNNResponse, GNNRunRequest
from neo_ange.expansion.readiness import DatasetReadinessReporter
from neo_ange.gnn.datasets import torch_geometric_available
from neo_ange.gnn.experiments import GNNExperimentRunner
from neo_ange.utils.serialization import to_jsonable

router = APIRouter(prefix="/gnn", tags=["gnn"])


@router.get("/status", response_model=GNNResponse)
def gnn_status(paths: Annotated[dict[str, Path], Depends(get_data_paths)]) -> GNNResponse:
    """Return dataset and graph readiness status."""
    readiness = DatasetReadinessReporter(
        data_dir=paths["data_dir"],
        silver_root=paths["silver_dir"],
        gold_root=paths["gold_dir"],
    ).build_report(write=True)
    graph_dir = paths["gnn_graph_dir"]
    nodes = _read_parquet(graph_dir / "nodes.parquet")
    edges = _read_parquet(graph_dir / "edges.parquet")
    reports = _latest_reports(paths["reports_dir"] / "gnn")
    return GNNResponse(
        status="ok",
        result={
            "dataset_readiness": readiness,
            "risk_scores_count": readiness["counts"]["risk_scores_count"],
            "graph_exists": not nodes.empty,
            "node_count": int(len(nodes)),
            "edge_count": int(len(edges)),
            "latest_reports": reports,
            "torch_geometric_available": torch_geometric_available(),
        },
    )


@router.post("/build-graph", response_model=GNNResponse)
def build_graph(
    request: GNNBuildGraphRequest,
    runner: Annotated[GNNExperimentRunner, Depends(get_gnn_runner)],
) -> GNNResponse:
    """Build and export the orbital similarity graph."""
    result = runner.run_graph_experiment(k=request.k, min_nodes=request.min_nodes)
    return GNNResponse(status=result["status"], result=result)


@router.post("/run", response_model=GNNResponse)
def run_gnn(
    request: GNNRunRequest,
    runner: Annotated[GNNExperimentRunner, Depends(get_gnn_runner)],
) -> GNNResponse:
    """Run baselines and optional GNN experiments."""
    result = runner.run_all(target=request.target, k=request.k, min_nodes=request.min_nodes)
    return GNNResponse(status=result["status"], result=result)


@router.get("/summary", response_model=GNNResponse)
def gnn_summary(paths: Annotated[dict[str, Path], Depends(get_data_paths)]) -> GNNResponse:
    """Return latest GNN markdown and JSON summaries when available."""
    report_dir = paths["reports_dir"] / "gnn"
    summary_path = report_dir / "gnn_summary.md"
    result_path = report_dir / "gnn_experiment_results.json"
    if not summary_path.exists() and not result_path.exists():
        return GNNResponse(status="missing_data", message="GNN summary report not found.")
    result: dict[str, Any] = {}
    if result_path.exists():
        result["experiment"] = json.loads(result_path.read_text(encoding="utf-8"))
    if summary_path.exists():
        result["markdown"] = summary_path.read_text(encoding="utf-8")
    return GNNResponse(status="success", result=to_jsonable(result))


@router.get("/graph", response_model=GNNResponse)
def get_graph(
    paths: Annotated[dict[str, Path], Depends(get_data_paths)],
    limit_nodes: int = 500,
) -> GNNResponse:
    """Return graph nodes and edges for API consumers."""
    graph_dir = paths["gnn_graph_dir"]
    nodes = _read_parquet(graph_dir / "nodes.parquet")
    edges = _read_parquet(graph_dir / "edges.parquet")
    summary = _read_json(paths["reports_dir"] / "gnn" / "graph_summary.json")
    if nodes.empty:
        return GNNResponse(
            status="missing_data",
            result={"nodes": [], "edges": [], "graph_summary": summary},
            message="Graph nodes not found. Run: python -m neo_ange.cli gnn build-graph",
        )
    limited_nodes = nodes.head(max(limit_nodes, 0))
    node_ids = set(limited_nodes["node_id"].astype(int).tolist()) if "node_id" in nodes else set()
    if not edges.empty and {"source", "target"}.issubset(edges.columns):
        limited_edges = edges[
            edges["source"].astype(int).isin(node_ids) & edges["target"].astype(int).isin(node_ids)
        ]
    else:
        limited_edges = pd.DataFrame()
    return GNNResponse(
        status="success",
        result={
            "nodes": to_jsonable(limited_nodes.to_dict(orient="records")),
            "edges": to_jsonable(limited_edges.to_dict(orient="records")),
            "graph_summary": summary,
        },
    )


@router.get("/metrics", response_model=GNNResponse)
def gnn_metrics(paths: Annotated[dict[str, Path], Depends(get_data_paths)]) -> GNNResponse:
    """Return latest GNN metrics table."""
    metrics = _read_csv(paths["reports_dir"] / "gnn" / "gnn_metrics.csv")
    if metrics.empty:
        return GNNResponse(status="missing_data", result={"metrics": []})
    metrics = _normalize_metrics(metrics)
    return GNNResponse(
        status="success", result={"metrics": to_jsonable(metrics.to_dict("records"))}
    )


@router.get("/object/{object_key}/neighbors", response_model=GNNResponse)
def object_neighbors(
    object_key: str,
    paths: Annotated[dict[str, Path], Depends(get_data_paths)],
) -> GNNResponse:
    """Return nearest graph neighbors for one object."""
    graph_dir = paths["gnn_graph_dir"]
    nodes = _read_parquet(graph_dir / "nodes.parquet")
    edges = _read_parquet(graph_dir / "edges.parquet")
    if nodes.empty or edges.empty or "object_key" not in nodes.columns:
        return GNNResponse(status="missing_data", result={"neighbors": []})
    matches = nodes[nodes["object_key"].astype("string") == str(object_key)]
    if matches.empty:
        return GNNResponse(
            status="not_found",
            result={"neighbors": []},
            message=f"Object '{object_key}' was not found in the graph.",
        )
    node_id = int(matches.iloc[0]["node_id"])
    incident = edges[
        (edges["source"].astype(int) == node_id) | (edges["target"].astype(int) == node_id)
    ]
    if incident.empty:
        return GNNResponse(status="success", result={"object_key": object_key, "neighbors": []})
    neighbor_ids = incident.apply(
        lambda row: int(row["target"]) if int(row["source"]) == node_id else int(row["source"]),
        axis=1,
    )
    neighbor_table = incident.copy()
    neighbor_table["neighbor_node_id"] = neighbor_ids
    node_lookup = nodes.set_index("node_id")
    neighbor_table["neighbor_object_key"] = neighbor_table["neighbor_node_id"].map(
        node_lookup["object_key"]
    )
    for column in ["risk_score_0_100", "risk_category", "pha", "des", "name", "full_name"]:
        if column in node_lookup.columns:
            neighbor_table[column] = neighbor_table["neighbor_node_id"].map(node_lookup[column])
    if "pha" not in neighbor_table.columns and "label" in node_lookup.columns:
        neighbor_table["pha"] = neighbor_table["neighbor_node_id"].map(node_lookup["label"])
    neighbor_table = neighbor_table.sort_values("similarity", ascending=False)
    return GNNResponse(
        status="success",
        result={
            "object_key": object_key,
            "neighbors": to_jsonable(neighbor_table.to_dict(orient="records")),
        },
    )


def _read_parquet(path: Path) -> pd.DataFrame:
    if path.exists():
        return pd.read_parquet(path)
    return pd.DataFrame()


def _read_csv(path: Path) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


def _normalize_metrics(metrics: pd.DataFrame) -> pd.DataFrame:
    normalized = metrics.copy()
    if "model_family" not in normalized.columns:
        normalized["model_family"] = normalized.get("family", "graph")
    if "target" not in normalized.columns:
        normalized["target"] = "pha"
    if "model_name" not in normalized.columns and "model" in normalized.columns:
        normalized["model_name"] = normalized["model"]
    normalized["interpretation"] = normalized.apply(
        lambda row: _metric_interpretation(row.to_dict()),
        axis=1,
    )
    return normalized


def _metric_interpretation(row: dict[str, Any]) -> str:
    if row.get("status") == "skipped_missing_dependency":
        return "Advanced GNN training was skipped because torch-geometric is unavailable."
    family = row.get("model_family") or row.get("family")
    feature_set = row.get("feature_set")
    if family == "gnn":
        return (
            "Graph neural evidence checks whether orbital neighborhoods improve label consistency."
        )
    if feature_set in {"full_features", "definition_features_only"}:
        return (
            "Leakage-sensitive diagnostic; useful internally but not preferred as "
            "user-facing evidence."
        )
    return "Secondary evidence for consistency between available features and observed labels."


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_reports(report_dir: Path) -> list[str]:
    if not report_dir.exists():
        return []
    return [
        str(path)
        for path in sorted(
            report_dir.glob("*"), key=lambda item: item.stat().st_mtime, reverse=True
        )
        if path.is_file()
    ][:5]
