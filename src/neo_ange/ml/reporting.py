"""Report writers for baseline ML experiments."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from neo_ange.utils.serialization import to_jsonable, write_json


def save_json_report(data: dict[str, Any], path: Path) -> Path:
    """Save a JSON report."""
    return write_json(data, path)


def save_metrics_csv(results: list[dict[str, Any]], path: Path) -> Path:
    """Save one row per experiment with key metrics flattened for quick review."""
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for result in results:
        metrics = result.get("metrics") if isinstance(result.get("metrics"), dict) else {}
        rows.append(
            {
                "status": result.get("status"),
                "feature_set_name": result.get("feature_set_name"),
                "model_name": result.get("model_name"),
                "n_samples": metrics.get("n_samples"),
                "positive_support": metrics.get("positive_support"),
                "negative_support": metrics.get("negative_support"),
                "accuracy": metrics.get("accuracy"),
                "precision": metrics.get("precision"),
                "recall": metrics.get("recall"),
                "f1": metrics.get("f1"),
                "false_negative_rate": metrics.get("false_negative_rate"),
                "roc_auc": metrics.get("roc_auc"),
                "pr_auc": metrics.get("pr_auc"),
                "brier_score": metrics.get("brier_score"),
                "model_path": result.get("model_path"),
                "warnings": " | ".join(result.get("warnings", [])),
                "errors": " | ".join(result.get("errors", [])),
            }
        )
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def generate_experiment_summary_markdown(results: dict[str, Any], path: Path) -> Path:
    """Generate a concise technical Markdown summary."""
    path.parent.mkdir(parents=True, exist_ok=True)
    validation = results.get("validation", {})
    experiments = results.get("experiments", [])
    best_pr_auc = _best_result(experiments, "pr_auc")
    best_f1 = _best_result(experiments, "f1")
    leakage = results.get("leakage_audit", {})

    lines = [
        "# Baseline ML Experiment Summary",
        "",
        "## Dataset",
        "",
        f"- Rows: {validation.get('n_rows', 0)}",
        f"- Positive PHA labels: {validation.get('n_positive', 0)}",
        f"- Negative PHA labels: {validation.get('n_negative', 0)}",
        f"- Positive rate: {_format_nullable(validation.get('positive_rate'))}",
        "",
        "## Experiments",
        "",
        f"- Status: {results.get('status')}",
        f"- Experiments attempted: {len(experiments)}",
        f"- Best PR-AUC: {_describe_best(best_pr_auc, 'pr_auc')}",
        f"- Best F1: {_describe_best(best_f1, 'f1')}",
        "",
        "## Leakage observations",
        "",
        leakage.get(
            "conclusion",
            "Leakage comparison was not available for this run.",
        ),
        "",
        "## Limitations",
        "",
        "- PHA can be close to a deterministic label when H and MOID are included.",
        "- Small or imbalanced datasets can make train-test metrics unstable.",
        "- These baselines do not represent a final risk-priority score.",
        "",
        "## Next steps",
        "",
        "- Run data expansion and ETL again to increase object coverage.",
        "- Compare definition-free features against the definition-related baseline.",
        "- Use these reports as preparation for a later risk-priority scoring phase.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def generate_insufficient_data_report(validation: dict[str, Any], path: Path) -> Path:
    """Write a Markdown report explaining why training was skipped."""
    path.parent.mkdir(parents=True, exist_ok=True)
    thresholds = validation.get("thresholds", {})
    lines = [
        "# Insufficient Data Report",
        "",
        "Baseline training was skipped because the current gold dataset does not satisfy "
        "the configured minimum volume or class-balance requirements.",
        "",
        "## Available labels",
        "",
        f"- Rows available: {validation.get('n_rows', 0)}",
        f"- Positive PHA labels: {validation.get('n_positive', 0)}",
        f"- Negative PHA labels: {validation.get('n_negative', 0)}",
        f"- Positive rate: {_format_nullable(validation.get('positive_rate'))}",
        "",
        "## Required thresholds",
        "",
        f"- Minimum rows: {thresholds.get('min_rows')}",
        f"- Minimum positive labels: {thresholds.get('min_positive')}",
        "",
        "Run data expansion and ETL again before training baselines.",
        "",
    ]
    warnings = validation.get("warnings", [])
    if warnings:
        lines.extend(["## Warnings", "", *[f"- {warning}" for warning in warnings], ""])
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _best_result(results: list[dict[str, Any]], metric_name: str) -> dict[str, Any] | None:
    eligible = [
        result
        for result in results
        if result.get("status") == "success"
        and isinstance(result.get("metrics"), dict)
        and result["metrics"].get(metric_name) is not None
    ]
    if not eligible:
        return None
    return max(eligible, key=lambda result: float(result["metrics"][metric_name]))


def _describe_best(result: dict[str, Any] | None, metric_name: str) -> str:
    if result is None:
        return "not available"
    value = result["metrics"].get(metric_name)
    return (
        f"{float(value):.4f} " f"({result.get('model_name')} on {result.get('feature_set_name')})"
    )


def _format_nullable(value: Any) -> str:
    if value is None:
        return "not available"
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return str(to_jsonable(value))
