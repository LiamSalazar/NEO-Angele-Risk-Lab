"""Benchmark report orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from neo_ange.benchmarks.api_benchmark import build_api_latency_benchmark
from neo_ange.benchmarks.dataset_scale import build_dataset_scale_report
from neo_ange.benchmarks.model_benchmark import build_model_benchmark
from neo_ange.benchmarks.runtime import build_runtime_report
from neo_ange.utils.serialization import to_jsonable, write_json


class BenchmarkRunner:
    """Generate technical benchmark reports for developers."""

    def __init__(
        self,
        gold_root: str | Path = "data/gold",
        reports_root: str | Path = "reports",
    ) -> None:
        self.gold_root = Path(gold_root)
        self.reports_root = Path(reports_root)
        self.report_dir = self.reports_root / "benchmarks"

    def run(self, write: bool = True) -> dict[str, Any]:
        """Build all benchmark reports."""
        dataset_scale = build_dataset_scale_report(self.gold_root, self.reports_root)
        runtime = build_runtime_report(".")
        model = build_model_benchmark(self.reports_root)
        try:
            api = build_api_latency_benchmark()
        except Exception as exc:
            api = {"status": "failed", "error": str(exc)}
        payload = {
            "status": "success",
            "dataset_scale": dataset_scale,
            "runtime": runtime,
            "model": model,
            "api_latency": api,
        }
        if write:
            payload["outputs"] = self.write_outputs(payload)
        return to_jsonable(payload)

    def status(self) -> dict[str, Any]:
        """Return benchmark report availability."""
        summary_path = self.report_dir / "benchmark_summary.md"
        scale_path = self.report_dir / "dataset_scale_1000_vs_4000.json"
        return {
            "status": "success" if summary_path.exists() or scale_path.exists() else "missing_data",
            "report_dir": str(self.report_dir),
            "summary_path": str(summary_path),
            "dataset_scale_path": str(scale_path),
        }

    def write_outputs(self, payload: dict[str, Any]) -> dict[str, str]:
        """Persist benchmark outputs."""
        self.report_dir.mkdir(parents=True, exist_ok=True)
        dataset_json = write_json(
            payload["dataset_scale"], self.report_dir / "dataset_scale_1000_vs_4000.json"
        )
        dataset_md = self.report_dir / "dataset_scale_1000_vs_4000.md"
        dataset_md.write_text(_render_dataset_scale(payload["dataset_scale"]), encoding="utf-8")
        runtime_json = write_json(payload["runtime"], self.report_dir / "runtime_benchmark.json")
        model_json = write_json(payload["model"], self.report_dir / "model_benchmark.json")
        api_json = write_json(
            payload["api_latency"], self.report_dir / "api_latency_benchmark.json"
        )
        summary_md = self.report_dir / "benchmark_summary.md"
        summary_md.write_text(_render_summary(payload), encoding="utf-8")
        return {
            "dataset_scale_json": str(dataset_json),
            "dataset_scale_markdown": str(dataset_md),
            "runtime_benchmark_json": str(runtime_json),
            "model_benchmark_json": str(model_json),
            "api_latency_benchmark_json": str(api_json),
            "benchmark_summary_markdown": str(summary_md),
        }


def _render_dataset_scale(report: dict[str, Any]) -> str:
    lines = [
        "# Dataset Scale 1000 vs 4000",
        "",
        f"- Target objects: {report.get('target_objects')}",
        f"- Current gold rows: {report.get('current_dataset', {}).get('gold_rows')}",
        f"- Current risk rows: {report.get('current_dataset', {}).get('risk_rows')}",
        f"- PHA distribution: {report.get('current_dataset', {}).get('pha_distribution')}",
        f"- Risk distribution: {report.get('current_dataset', {}).get('risk_distribution')}",
        f"- GNN nodes: {report.get('current_dataset', {}).get('gnn_nodes')}",
        f"- GNN edges: {report.get('current_dataset', {}).get('gnn_edges')}",
        f"- Recommendation: {report.get('recommendation')}",
        "",
        "The 4000-object comparison remains pending until expansion and rebuild complete.",
        "",
    ]
    return "\n".join(lines)


def _render_summary(payload: dict[str, Any]) -> str:
    dataset = payload["dataset_scale"]
    runtime = payload["runtime"]
    api = payload["api_latency"]
    return "\n".join(
        [
            "# Benchmark Summary",
            "",
            f"- Dataset-scale status: {dataset.get('status')}",
            f"- Current rows: {dataset.get('current_dataset', {}).get('gold_rows')}",
            f"- Artifact count: {runtime.get('artifact_count')}",
            f"- API benchmark status: {api.get('status')}",
            "",
            dataset.get("recommendation", ""),
            "",
        ]
    )
