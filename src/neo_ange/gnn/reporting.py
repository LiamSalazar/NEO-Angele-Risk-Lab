"""Static report writers for GNN research experiments."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from neo_ange.utils.serialization import write_json


class GNNReportWriter:
    """Write JSON, CSV, and markdown outputs for graph experiments."""

    def __init__(self, report_dir: str | Path = "reports/gnn") -> None:
        self.report_dir = Path(report_dir)

    def write_outputs(self, result: dict[str, Any]) -> dict[str, str]:
        """Persist experiment result, metrics table, and markdown summary."""
        self.report_dir.mkdir(parents=True, exist_ok=True)
        json_path = write_json(result, self.report_dir / "gnn_experiment_results.json")
        metrics_path = self.report_dir / "gnn_metrics.csv"
        metric_rows = _metric_rows(result)
        pd.DataFrame(metric_rows).to_csv(metrics_path, index=False)
        k_ablation_csv, k_ablation_json, k_ablation_md = self._write_k_ablation(
            result.get("graph_k_ablation", {})
        )
        benchmark_csv, benchmark_md = self._write_benchmark(metric_rows)
        summary_path = self.report_dir / "gnn_summary.md"
        summary_path.write_text(render_summary(result), encoding="utf-8")
        return {
            "gnn_experiment_results": str(json_path),
            "gnn_metrics": str(metrics_path),
            "gnn_summary": str(summary_path),
            "graph_k_ablation_csv": str(k_ablation_csv),
            "graph_k_ablation_summary_json": str(k_ablation_json),
            "graph_k_ablation_summary_markdown": str(k_ablation_md),
            "gnn_vs_tabular_benchmark_csv": str(benchmark_csv),
            "gnn_vs_tabular_benchmark_summary_markdown": str(benchmark_md),
        }

    def _write_k_ablation(self, payload: dict[str, Any]) -> tuple[Path, Path, Path]:
        rows = payload.get("rows", []) if isinstance(payload, dict) else []
        csv_path = self.report_dir / "graph_k_ablation.csv"
        pd.DataFrame(rows).to_csv(csv_path, index=False)
        summary = {
            "status": (
                payload.get("status", "missing_data")
                if isinstance(payload, dict)
                else "missing_data"
            ),
            "k_values": [row.get("k") for row in rows],
            "max_edges": max((row.get("edges", 0) for row in rows), default=0),
            "min_connected_components": min(
                (row.get("connected_components", 0) for row in rows),
                default=0,
            ),
            "interpretation": (
                "k controls graph density. Higher k can improve connectivity but may blur local "
                "orbital neighborhoods."
            ),
        }
        json_path = write_json(summary, self.report_dir / "graph_k_ablation_summary.json")
        md_path = self.report_dir / "graph_k_ablation_summary.md"
        md_path.write_text(_render_k_ablation_summary(summary, rows), encoding="utf-8")
        return csv_path, json_path, md_path

    def _write_benchmark(self, rows: list[dict[str, Any]]) -> tuple[Path, Path]:
        benchmark_rows = []
        best_tabular = _best_f1(row for row in rows if row.get("family") == "baseline")
        best_gnn = _best_f1(row for row in rows if row.get("family") == "gnn")
        for row in rows:
            feature_set = str(row.get("feature_set"))
            benchmark_rows.append(
                {
                    **row,
                    "leakage_sensitive": feature_set
                    in {
                        "graph_node_features",
                        "graph_node_features_without_risk_score",
                        "graph_node_features_with_risk_score",
                    },
                    "transductive_setting": row.get("family") == "gnn",
                    "improves_over_best_tabular": (
                        bool(
                            row.get("family") == "gnn"
                            and best_tabular is not None
                            and row.get("f1") is not None
                            and float(row["f1"]) > best_tabular
                        )
                    ),
                }
            )
        csv_path = self.report_dir / "gnn_vs_tabular_benchmark.csv"
        pd.DataFrame(benchmark_rows).to_csv(csv_path, index=False)
        md_path = self.report_dir / "gnn_vs_tabular_benchmark_summary.md"
        md_path.write_text(_render_benchmark_summary(best_tabular, best_gnn), encoding="utf-8")
        return csv_path, md_path


def render_summary(result: dict[str, Any]) -> str:
    """Render a concise, honest markdown summary of graph experiments."""
    graph = result.get("graph_summary", {})
    baseline = result.get("baseline_metrics", {})
    gnn = result.get("gnn_metrics", {})
    improved = _improvement_statement(baseline, gnn)
    lines = [
        "# GNN research lab summary",
        "",
        f"Status: **{result.get('status', 'unknown')}**",
        "",
        "## Dataset and graph",
        "",
        f"- Nodes: {graph.get('n_nodes', result.get('n_nodes', 0))}",
        f"- Edges: {graph.get('n_edges', result.get('n_edges', 0))}",
        f"- Density: {graph.get('density', 0)}",
        f"- Construction: kNN orbital similarity, k={result.get('k')}",
        f"- Target: {result.get('target')}",
        "",
        "## Features",
        "",
        "- Orbital elements, close-approach aggregates, Sentry signals, physical proxies, "
        "and experimental risk score where available.",
        "- PHA labels and object identifiers are excluded from similarity features.",
        "",
        "## Baseline metrics",
        "",
    ]
    if baseline:
        for feature_set, models in baseline.items():
            lines.append(f"### {feature_set}")
            for model_name, payload in models.items():
                metrics = payload.get("metrics", {})
                lines.append(
                    f"- {model_name}: status={payload.get('status')}, "
                    f"f1={metrics.get('f1')}, roc_auc={metrics.get('roc_auc')}"
                )
    else:
        lines.append("- No baseline metrics were generated.")
    lines.extend(["", "## GNN metrics", ""])
    if gnn:
        for model_name, payload in gnn.items():
            metrics = payload.get("metrics", {})
            lines.append(
                f"- {model_name}: status={payload.get('status')}, "
                f"f1={metrics.get('f1')}, roc_auc={metrics.get('roc_auc')}"
            )
    else:
        lines.append("- Real GNN metrics were not generated.")
    lines.extend(
        [
            "",
            "## Comparison",
            "",
            improved,
            "",
            "## Leakage considerations",
            "",
            "- The target label is not used as a node feature or similarity feature.",
            "- Definition-adjacent PHA features are isolated in baseline feature sets "
            "for honest comparison.",
            "- The GNN setting is transductive when test nodes remain in the graph; it is not "
            "claimed as inductive generalization.",
            "",
            "## Limitations",
            "",
        ]
    )
    warnings = result.get("warnings", [])
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("- No major limitations were reported by the runner.")
    lines.extend(
        [
            "",
            "## Next steps for frontend",
            "",
            "- Show graph readiness, neighbors, model comparison, and honest warnings.",
            "- Avoid presenting GNN as superior unless metrics demonstrate it on current data.",
            "",
        ]
    )
    return "\n".join(lines)


def _metric_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family, family_metrics in (
        ("baseline", result.get("baseline_metrics", {})),
        ("gnn", result.get("gnn_metrics", {})),
    ):
        if family == "baseline":
            for feature_set, models in family_metrics.items():
                for model_name, payload in models.items():
                    rows.append(_metric_row(family, model_name, payload, feature_set=feature_set))
        else:
            for model_name, payload in family_metrics.items():
                rows.append(_metric_row(family, model_name, payload, feature_set="graph"))
    return rows


def _metric_row(
    family: str,
    model_name: str,
    payload: dict[str, Any],
    feature_set: str,
) -> dict[str, Any]:
    metrics = payload.get("metrics", {})
    return {
        "family": family,
        "model_name": model_name,
        "feature_set": feature_set,
        "status": payload.get("status"),
        "accuracy": metrics.get("accuracy"),
        "precision": metrics.get("precision"),
        "recall": metrics.get("recall"),
        "f1": metrics.get("f1"),
        "roc_auc": metrics.get("roc_auc"),
        "pr_auc": metrics.get("pr_auc"),
        "false_negative_rate": metrics.get("false_negative_rate"),
    }


def _improvement_statement(
    baseline: dict[str, Any],
    gnn: dict[str, Any],
) -> str:
    baseline_best = _best_f1_from_baselines(baseline)
    gnn_best = _best_f1_from_gnn(gnn)
    if gnn_best is None:
        return "Real GNN training did not produce comparable metrics for this run."
    if baseline_best is None:
        return "Baselines did not produce comparable metrics, so no superiority claim is possible."
    if gnn_best > baseline_best:
        return (
            f"Best GNN F1 ({gnn_best:.3f}) exceeded best baseline F1 "
            f"({baseline_best:.3f}) in this run."
        )
    return (
        f"Best GNN F1 ({gnn_best:.3f}) did not exceed best baseline F1 "
        f"({baseline_best:.3f}) in this run."
    )


def _best_f1_from_baselines(baseline: dict[str, Any]) -> float | None:
    values: list[float] = []
    for models in baseline.values():
        for payload in models.values():
            value = payload.get("metrics", {}).get("f1")
            if value is not None:
                values.append(float(value))
    return max(values) if values else None


def _render_k_ablation_summary(summary: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Graph k Ablation Summary",
        "",
        summary.get("interpretation", ""),
        "",
    ]
    for row in rows:
        lines.append(
            f"- k={row.get('k')}: nodes={row.get('nodes')}, edges={row.get('edges')}, "
            f"density={row.get('density')}, components={row.get('connected_components')}"
        )
    lines.append("")
    return "\n".join(lines)


def _render_benchmark_summary(best_tabular: float | None, best_gnn: float | None) -> str:
    lines = [
        "# GNN vs Tabular Benchmark",
        "",
        "Graph models are experimental secondary evidence. The Risk Priority Score remains "
        "the ranking source.",
        "",
        f"- Best tabular F1: {best_tabular}",
        f"- Best GNN F1: {best_gnn}",
        "",
    ]
    if best_gnn is None:
        lines.append("No comparable GNN metric was produced in this run.")
    elif best_tabular is None:
        lines.append("No comparable tabular metric was produced, so no superiority claim is made.")
    elif best_gnn > best_tabular:
        lines.append("Best GNN F1 exceeded best tabular F1 in this run.")
    else:
        lines.append("Best GNN F1 did not exceed best tabular F1 in this run.")
    lines.extend(
        [
            "",
            "The setting is transductive if test nodes are present in the graph; labels must not "
            "be used to construct edges.",
            "",
        ]
    )
    return "\n".join(lines)


def _best_f1(rows: Any) -> float | None:
    values: list[float] = []
    for row in rows:
        value = row.get("f1")
        if value is not None:
            try:
                values.append(float(value))
            except (TypeError, ValueError):
                continue
    return max(values) if values else None


def _best_f1_from_gnn(gnn: dict[str, Any]) -> float | None:
    values: list[float] = []
    for payload in gnn.values():
        value = payload.get("metrics", {}).get("f1")
        if value is not None:
            values.append(float(value))
    return max(values) if values else None
