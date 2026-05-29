"""Build and export orbital similarity graphs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import networkx as nx
import pandas as pd

from neo_ange.domain.graph import OrbitalGraph, OrbitalGraphNode
from neo_ange.gnn.schemas import GRAPH_NODE_FEATURES, GRAPH_VERSION
from neo_ange.gnn.similarity import OrbitalSimilarityCalculator
from neo_ange.utils.serialization import to_jsonable, write_json


class OrbitalGraphBuilder:
    """Build an orbital similarity graph from scored asteroid rows."""

    def __init__(
        self,
        gold_root: str | Path = "data/gold",
        report_dir: str | Path = "reports/gnn",
        similarity_calculator: OrbitalSimilarityCalculator | None = None,
    ) -> None:
        self.gold_root = Path(gold_root)
        self.report_dir = Path(report_dir)
        self.similarity = similarity_calculator or OrbitalSimilarityCalculator()
        self.risk_scores_dir = self.gold_root / "risk_scores"
        self.gold_features_dir = self.gold_root / "neo_risk_features"

    def build_graph_from_risk_scores(
        self,
        k: int = 10,
        target: str = "pha",
        min_nodes: int = 100,
    ) -> OrbitalGraph:
        """Build a kNN orbital graph from risk scores, or report insufficient data."""
        df = self._load_source_dataframe()
        if len(df) < min_nodes:
            graph = OrbitalGraph(nodes=[], edges=[], graph_version=GRAPH_VERSION)
            self._write_graph_summary(
                graph,
                source_df=df,
                target=target,
                status="insufficient_data",
                warnings=[
                    f"Need at least {min_nodes} nodes for GNN graph construction; found {len(df)}."
                ],
            )
            return graph
        nodes = self._build_nodes(df, target=target)
        edges = self.similarity.compute_knn_edges(df, k=k)
        graph = OrbitalGraph(nodes=nodes, edges=edges, graph_version=GRAPH_VERSION)
        self._write_graph_summary(graph, source_df=df, target=target, status="success", warnings=[])
        return graph

    def build_networkx_graph(self, graph: OrbitalGraph) -> nx.Graph:
        """Build a NetworkX graph from the domain graph."""
        return graph.to_networkx()

    def export_graph(
        self,
        graph: OrbitalGraph,
        output_dir: str | Path = "data/gold/gnn_graph",
    ) -> dict[str, Any]:
        """Persist graph nodes, edges, and a summary report."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        nodes_path = output_path / "nodes.parquet"
        edges_path = output_path / "edges.parquet"
        pd.DataFrame([node.to_dict() for node in graph.nodes]).to_parquet(nodes_path)
        pd.DataFrame([edge.to_dict() for edge in graph.edges]).to_parquet(edges_path)
        status = "success" if graph.nodes else "insufficient_data"
        warnings = [] if graph.nodes else ["No graph nodes were exported; data is insufficient."]
        summary = self.graph_summary(graph, status=status, warnings=warnings)
        summary_path = write_json(summary, self.report_dir / "graph_summary.json")
        return {
            "nodes_path": str(nodes_path),
            "edges_path": str(edges_path),
            "graph_summary_path": str(summary_path),
            "graph_summary": summary,
        }

    def graph_summary(
        self,
        graph: OrbitalGraph,
        status: str = "success",
        warnings: list[str] | None = None,
    ) -> dict[str, Any]:
        """Return graph statistics for reports and APIs."""
        nx_graph = graph.to_networkx()
        degrees = [degree for _, degree in nx_graph.degree()]
        target_distribution: dict[str, int] = {}
        risk_category_distribution: dict[str, int] = {}
        for node in graph.nodes:
            target_key = str(node.label) if node.label is not None else "unknown"
            target_distribution[target_key] = target_distribution.get(target_key, 0) + 1
            category = node.risk_category or "unknown"
            risk_category_distribution[category] = risk_category_distribution.get(category, 0) + 1
        return to_jsonable(
            {
                "status": status,
                "graph_version": graph.graph_version,
                "n_nodes": graph.node_count(),
                "n_edges": graph.edge_count(),
                "density": graph.density(),
                "connected_components": (
                    nx.number_connected_components(nx_graph) if graph.node_count() else 0
                ),
                "avg_degree": float(sum(degrees) / len(degrees)) if degrees else 0.0,
                "target_distribution": target_distribution,
                "risk_category_distribution": risk_category_distribution,
                "warnings": warnings or [],
            }
        )

    def _build_nodes(self, df: pd.DataFrame, target: str) -> list[OrbitalGraphNode]:
        nodes: list[OrbitalGraphNode] = []
        feature_columns = [column for column in GRAPH_NODE_FEATURES if column in df.columns]
        for node_id, (_, row) in enumerate(df.reset_index(drop=True).iterrows()):
            object_key = _object_key(row)
            features = {
                column: _json_value(row.get(column))
                for column in feature_columns
                if _json_value(row.get(column)) is not None
            }
            nodes.append(
                OrbitalGraphNode(
                    node_id=node_id,
                    object_key=object_key,
                    features=features,
                    label=_label_value(row.get(target)),
                    risk_score_0_100=_float_or_none(row.get("risk_score_0_100")),
                    risk_category=_string_or_none(row.get("risk_category")),
                )
            )
        return nodes

    def _load_source_dataframe(self) -> pd.DataFrame:
        risk = _read_parquet(self.risk_scores_dir / "risk_scores.parquet")
        if risk.empty:
            risk = _read_parquet(self.risk_scores_dir)
        if not risk.empty:
            return risk.reset_index(drop=True)
        return _read_parquet(self.gold_features_dir).reset_index(drop=True)

    def _write_graph_summary(
        self,
        graph: OrbitalGraph,
        source_df: pd.DataFrame,
        target: str,
        status: str,
        warnings: list[str],
    ) -> Path:
        summary = self.graph_summary(graph, status=status, warnings=warnings)
        summary["source_row_count"] = int(len(source_df))
        summary["target"] = target
        if target in source_df.columns:
            summary["source_target_distribution"] = (
                source_df[target].astype("string").fillna("unknown").value_counts().to_dict()
            )
        return write_json(summary, self.report_dir / "graph_summary.json")


def _read_parquet(path: Path) -> pd.DataFrame:
    if path.is_file():
        return pd.read_parquet(path)
    if path.is_dir() and any(path.glob("*.parquet")):
        return pd.read_parquet(path)
    return pd.DataFrame()


def _object_key(row: pd.Series) -> str:
    for column in ("object_key", "spkid", "des", "full_name", "name"):
        value = row.get(column)
        if _string_or_none(value):
            return str(value)
    return "unknown-object"


def _label_value(value: Any) -> int | float | str | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, bool):
        return int(value)
    text = str(value).strip().lower()
    if text in {"true", "t", "1", "yes", "y"}:
        return 1
    if text in {"false", "f", "0", "no", "n"}:
        return 0
    return value


def _json_value(value: Any) -> Any:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, bool):
        return int(value)
    if hasattr(value, "item"):
        return value.item()
    return value


def _float_or_none(value: Any) -> float | None:
    value = _json_value(value)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _string_or_none(value: Any) -> str | None:
    value = _json_value(value)
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None
