"""Machine-learning pipeline orchestration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from neo_ange.manifests.run_manifest import (
    RunManifest,
    create_run_id,
    save_manifest,
    utc_now_manifest,
)
from neo_ange.ml.dataset import MLDatasetLoader
from neo_ange.ml.experiments import BaselineExperimentRunner
from neo_ange.ml.leakage import LeakageAuditor


class MLPipeline:
    """Coordinate baseline training, leakage audit, and report generation."""

    def __init__(
        self,
        gold_root: str | Path = "data/gold",
        output_dir: str | Path = "reports/ml",
        model_dir: str | Path = "artifacts/models",
        random_state: int = 42,
    ) -> None:
        self.gold_root = Path(gold_root)
        self.output_dir = Path(output_dir)
        self.model_dir = Path(model_dir)
        self.random_state = random_state

    def run_baselines(
        self,
        target: str = "pha",
        min_rows: int = 100,
        min_positive: int = 5,
    ) -> dict[str, Any]:
        """Run baseline experiments or produce insufficient-data reports."""
        runner = BaselineExperimentRunner(
            output_dir=self.output_dir,
            random_state=self.random_state,
            gold_root=self.gold_root,
            model_dir=self.model_dir,
        )
        result = runner.run_all_baselines(
            target=target,
            min_rows=min_rows,
            min_positive=min_positive,
        )
        return _pipeline_result(result, target=target)

    def run_leakage_audit(self, target: str = "pha") -> dict[str, Any]:
        """Generate a leakage audit from the latest baseline results when available."""
        started_at = utc_now_manifest()
        run_id = create_run_id("ml")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        baseline_path = self.output_dir / "baseline_results.json"
        warnings: list[str] = []
        errors: list[str] = []
        experiments: list[dict[str, Any]] = []

        if baseline_path.exists():
            payload = json.loads(baseline_path.read_text(encoding="utf-8"))
            experiments = payload.get("experiments", [])
            if not experiments:
                warnings.append(
                    "No completed baseline experiments were available; leakage report will "
                    "explain the limitation."
                )
        else:
            validation = MLDatasetLoader(self.gold_root).validate_target(
                MLDatasetLoader(self.gold_root).load_gold_features(),
                target=target,
            )
            warnings.append(
                "No baseline_results.json was found. Run baseline training before interpreting "
                "leakage comparisons."
            )
            experiments = [
                {
                    "status": "skipped",
                    "feature_set_name": "not_available",
                    "model_name": "not_available",
                    "features": [],
                    "metrics": {},
                    "warnings": validation.get("warnings", []),
                    "errors": [],
                }
            ]

        auditor = LeakageAuditor()
        markdown_path = auditor.generate_leakage_report(experiments, output_dir=self.output_dir)
        json_path = self.output_dir / "leakage_audit.json"
        comparison = auditor.compare_feature_sets(experiments)
        status = (
            "success" if comparison["status"] != "insufficient_results" else "insufficient_data"
        )
        result = {
            "status": status,
            "target": target,
            "outputs": {
                "leakage_audit_json": str(json_path),
                "leakage_audit_markdown": str(markdown_path),
            },
            "metrics_summary": comparison,
            "warnings": warnings,
            "errors": errors,
        }
        manifest_path = self._save_manifest(run_id, started_at, result)
        result["outputs"]["manifest_path"] = str(manifest_path)
        return result

    def run_all(self, target: str = "pha") -> dict[str, Any]:
        """Run baseline training and then refresh leakage audit outputs."""
        baseline_result = self.run_baselines(target=target)
        leakage_result = self.run_leakage_audit(target=target)
        status = _combine_statuses(baseline_result["status"], leakage_result["status"])
        return {
            "status": status,
            "target": target,
            "outputs": {
                **baseline_result.get("outputs", {}),
                **leakage_result.get("outputs", {}),
            },
            "metrics_summary": baseline_result.get("metrics_summary", {}),
            "warnings": [
                *baseline_result.get("warnings", []),
                *leakage_result.get("warnings", []),
            ],
            "errors": [
                *baseline_result.get("errors", []),
                *leakage_result.get("errors", []),
            ],
        }

    def _save_manifest(
        self,
        run_id: str,
        started_at: str,
        result: dict[str, Any],
    ) -> Path:
        manifest = RunManifest(
            run_id=run_id,
            run_type="ml",
            started_at_utc=started_at,
            ended_at_utc=utc_now_manifest(),
            status=result["status"],
            inputs={"target": result.get("target"), "gold_root": str(self.gold_root)},
            outputs=result.get("outputs", {}),
            metrics=result.get("metrics_summary", {}),
            warnings=result.get("warnings", []),
            errors=result.get("errors", []),
        )
        return save_manifest(manifest)


def _pipeline_result(result: dict[str, Any], target: str) -> dict[str, Any]:
    return {
        "status": result.get("status", "failed"),
        "target": target,
        "outputs": result.get("outputs", {}),
        "metrics_summary": result.get("metrics_summary", {}),
        "warnings": result.get("warnings", []),
        "errors": result.get("errors", []),
        "validation": result.get("validation", {}),
    }


def _combine_statuses(first: str, second: str) -> str:
    if "failed" in {first, second}:
        return "failed"
    if first == "insufficient_data":
        return "insufficient_data"
    if second == "insufficient_data":
        return "partial_success" if first == "success" else "insufficient_data"
    if "partial_success" in {first, second}:
        return "partial_success"
    return "success"
