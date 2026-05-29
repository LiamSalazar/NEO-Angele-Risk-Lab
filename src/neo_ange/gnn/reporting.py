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
        pd.DataFrame(_metric_rows(result)).to_csv(metrics_path, index=False)
        summary_path = self.report_dir / "gnn_summary.md"
        summary_path.write_text(render_summary(result), encoding="utf-8")
        return {
            "gnn_experiment_results": str(json_path),
            "gnn_metrics": str(metrics_path),
            "gnn_summary": str(summary_path),
        }


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


def _best_f1_from_gnn(gnn: dict[str, Any]) -> float | None:
    values: list[float] = []
    for payload in gnn.values():
        value = payload.get("metrics", {}).get("f1")
        if value is not None:
            values.append(float(value))
    return max(values) if values else None
