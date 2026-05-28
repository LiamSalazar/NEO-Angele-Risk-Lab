"""Experiment runner for leakage-aware baseline ML models."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from neo_ange.manifests.run_manifest import (
    RunManifest,
    create_run_id,
    save_manifest,
    utc_now_manifest,
)
from neo_ange.ml.baselines import (
    RULE_BASED_PHA_MODEL,
    build_model_pipeline,
    default_model_names,
)
from neo_ange.ml.dataset import MLDatasetLoader
from neo_ange.ml.feature_sets import FeatureSetRegistry
from neo_ange.ml.leakage import LeakageAuditor
from neo_ange.ml.metrics import calculate_classification_metrics
from neo_ange.ml.preprocessing import split_dataset
from neo_ange.ml.reporting import (
    generate_experiment_summary_markdown,
    generate_insufficient_data_report,
    save_json_report,
    save_metrics_csv,
)

FEATURE_SETS_TO_RUN = [
    "full_features",
    "definition_features_only",
    "no_definition_features",
    "orbital_only",
    "approach_and_quality",
    "sentry_related",
]


class BaselineExperimentRunner:
    """Run baseline classifiers across feature sets and write reports."""

    def __init__(
        self,
        output_dir: str | Path = "reports/ml",
        random_state: int = 42,
        gold_root: str | Path = "data/gold",
        model_dir: str | Path = "artifacts/models",
    ) -> None:
        self.output_dir = Path(output_dir)
        self.random_state = random_state
        self.gold_root = Path(gold_root)
        self.model_dir = Path(model_dir)
        self.loader = MLDatasetLoader(self.gold_root)
        self.feature_sets = FeatureSetRegistry()
        self.leakage_auditor = LeakageAuditor()

    def run_experiment(
        self,
        df: pd.DataFrame,
        target: str,
        feature_set_name: str,
        model_name: str,
    ) -> dict[str, Any]:
        """Run one feature-set/model experiment and return serializable results."""
        warnings: list[str] = []
        errors: list[str] = []
        if target not in df.columns:
            return _skipped_result(
                feature_set_name,
                model_name,
                [f"Target column '{target}' is missing."],
            )

        resolved = self.feature_sets.resolve(df, feature_set_name, target=target)
        warnings.extend(resolved["warnings"])
        features = resolved["features"]
        if model_name == RULE_BASED_PHA_MODEL:
            features = [feature for feature in ["h", "moid"] if feature in df.columns]
        if not features:
            return _skipped_result(
                feature_set_name,
                model_name,
                warnings + [f"Feature set '{feature_set_name}' has no usable features."],
            )

        y = pd.to_numeric(df[target], errors="coerce").astype("int64")
        X = df[features].copy()
        try:
            X_train, X_test, y_train, y_test, split_warnings = split_dataset(
                X,
                y,
                random_state=self.random_state,
            )
            warnings.extend(split_warnings)
            model = build_model_pipeline(model_name, features, random_state=self.random_state)
            model.fit(X_train, y_train)
            predictions = model.predict(X_test)
            probabilities = _predict_proba(model, X_test)
            metrics = calculate_classification_metrics(y_test, predictions, probabilities)
            warnings.extend(metrics.get("warnings", []))
            model_path = self._save_model(model, feature_set_name, model_name)
            return {
                "status": "success",
                "feature_set_name": feature_set_name,
                "model_name": model_name,
                "target": target,
                "features": features,
                "missing_features": resolved["missing_features"],
                "metrics": metrics,
                "model_path": str(model_path),
                "warnings": warnings,
                "errors": errors,
            }
        except Exception as exc:
            errors.append(str(exc))
            return {
                "status": "failed",
                "feature_set_name": feature_set_name,
                "model_name": model_name,
                "target": target,
                "features": features,
                "missing_features": resolved["missing_features"],
                "metrics": {},
                "model_path": None,
                "warnings": warnings,
                "errors": errors,
            }

    def run_all_baselines(
        self,
        target: str = "pha",
        min_rows: int = 100,
        min_positive: int = 5,
    ) -> dict[str, Any]:
        """Run all baseline experiments or write an insufficient-data report."""
        started_at = utc_now_manifest()
        run_id = create_run_id("ml")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        df = self.loader.prepare_training_frame(target=target)
        validation = self.loader.validate_target(df, target=target)
        validation["thresholds"] = {"min_rows": min_rows, "min_positive": min_positive}
        validation_warnings = list(validation.get("warnings", []))

        if validation["status"] != "ok":
            return self._write_insufficient_results(
                run_id=run_id,
                started_at=started_at,
                target=target,
                validation=validation,
                warnings=validation_warnings,
            )

        if validation["n_rows"] < min_rows:
            validation_warnings.append(
                f"Gold dataset has {validation['n_rows']} rows; {min_rows} are required."
            )
        if validation["n_positive"] < min_positive:
            validation_warnings.append(
                "Gold dataset has "
                f"{validation['n_positive']} positive labels; {min_positive} are required."
            )
        if validation_warnings:
            validation["warnings"] = validation_warnings
            return self._write_insufficient_results(
                run_id=run_id,
                started_at=started_at,
                target=target,
                validation=validation,
                warnings=validation_warnings,
            )

        model_names = default_model_names(include_hist_gradient=len(df) >= 50)
        experiments: list[dict[str, Any]] = []
        for feature_set_name in FEATURE_SETS_TO_RUN:
            for model_name in model_names:
                experiments.append(
                    self.run_experiment(
                        df=df,
                        target=target,
                        feature_set_name=feature_set_name,
                        model_name=model_name,
                    )
                )
            if {"h", "moid"}.issubset(df.columns) and feature_set_name in {
                "full_features",
                "definition_features_only",
            }:
                experiments.append(
                    self.run_experiment(
                        df=df,
                        target=target,
                        feature_set_name=feature_set_name,
                        model_name=RULE_BASED_PHA_MODEL,
                    )
                )

        leakage_path = self.leakage_auditor.generate_leakage_report(
            experiments,
            output_dir=self.output_dir,
        )
        leakage_json = self.output_dir / "leakage_audit.json"
        leakage_comparison = self.leakage_auditor.compare_feature_sets(experiments)
        if all(result["status"] == "success" for result in experiments):
            status = "success"
        elif any(result["status"] == "success" for result in experiments):
            status = "partial_success"
        else:
            status = "failed"
        outputs = self._write_reports(
            status=status,
            validation=validation,
            experiments=experiments,
            leakage_audit=leakage_comparison,
            extra_outputs={
                "leakage_audit_json": str(leakage_json),
                "leakage_audit_markdown": str(leakage_path),
            },
        )
        result = {
            "status": status,
            "target": target,
            "validation": validation,
            "experiments": experiments,
            "outputs": outputs,
            "metrics_summary": _metrics_summary(experiments),
            "leakage_audit": leakage_comparison,
            "warnings": _collect_messages(experiments, "warnings"),
            "errors": _collect_messages(experiments, "errors"),
        }
        manifest_path = self._save_manifest(run_id, started_at, result)
        result["outputs"]["manifest_path"] = str(manifest_path)
        return result

    def _write_insufficient_results(
        self,
        run_id: str,
        started_at: str,
        target: str,
        validation: dict[str, Any],
        warnings: list[str],
    ) -> dict[str, Any]:
        result = {
            "status": "insufficient_data",
            "target": target,
            "validation": validation,
            "experiments": [],
            "outputs": {},
            "metrics_summary": {},
            "warnings": warnings,
            "errors": [],
        }
        baseline_results_path = self.output_dir / "baseline_results.json"
        metrics_csv_path = self.output_dir / "baseline_metrics.csv"
        insufficient_path = self.output_dir / "insufficient_data_report.md"
        result["outputs"] = {
            "baseline_results_json": str(baseline_results_path),
            "baseline_metrics_csv": str(metrics_csv_path),
            "insufficient_data_report": str(insufficient_path),
        }
        save_json_report(result, baseline_results_path)
        save_metrics_csv([], metrics_csv_path)
        generate_insufficient_data_report(validation, insufficient_path)
        manifest_path = self._save_manifest(run_id, started_at, result)
        result["outputs"]["manifest_path"] = str(manifest_path)
        save_json_report(result, baseline_results_path)
        return result

    def _write_reports(
        self,
        status: str,
        validation: dict[str, Any],
        experiments: list[dict[str, Any]],
        leakage_audit: dict[str, Any],
        extra_outputs: dict[str, str],
    ) -> dict[str, str]:
        baseline_results_path = self.output_dir / "baseline_results.json"
        metrics_csv_path = self.output_dir / "baseline_metrics.csv"
        summary_path = self.output_dir / "experiment_summary.md"
        outputs = {
            "baseline_results_json": str(baseline_results_path),
            "baseline_metrics_csv": str(metrics_csv_path),
            "experiment_summary_markdown": str(summary_path),
            **extra_outputs,
        }
        results_payload = {
            "status": status,
            "validation": validation,
            "experiments": experiments,
            "metrics_summary": _metrics_summary(experiments),
            "leakage_audit": leakage_audit,
            "outputs": outputs,
        }
        save_json_report(results_payload, baseline_results_path)
        save_metrics_csv(experiments, metrics_csv_path)
        generate_experiment_summary_markdown(results_payload, summary_path)
        return outputs

    def _save_model(self, model: Any, feature_set_name: str, model_name: str) -> Path:
        self.model_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{_safe_name(feature_set_name)}__{_safe_name(model_name)}.joblib"
        path = self.model_dir / filename
        joblib.dump(model, path)
        return path

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
            inputs={
                "target": result.get("target"),
                "gold_root": str(self.gold_root),
                "output_dir": str(self.output_dir),
            },
            outputs=result.get("outputs", {}),
            metrics=result.get("metrics_summary", {}),
            warnings=result.get("warnings", []),
            errors=result.get("errors", []),
        )
        return save_manifest(manifest)


def _skipped_result(
    feature_set_name: str,
    model_name: str,
    warnings: list[str],
) -> dict[str, Any]:
    return {
        "status": "skipped",
        "feature_set_name": feature_set_name,
        "model_name": model_name,
        "features": [],
        "missing_features": [],
        "metrics": {},
        "model_path": None,
        "warnings": warnings,
        "errors": [],
    }


def _predict_proba(model: Any, X_test: pd.DataFrame) -> Any:
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X_test)
    return None


def _metrics_summary(experiments: list[dict[str, Any]]) -> dict[str, Any]:
    successful = [
        result
        for result in experiments
        if result.get("status") == "success" and isinstance(result.get("metrics"), dict)
    ]
    return {
        "experiments_attempted": len(experiments),
        "experiments_successful": len(successful),
        "best_pr_auc": _best_metric(successful, "pr_auc"),
        "best_f1": _best_metric(successful, "f1"),
    }


def _best_metric(results: list[dict[str, Any]], metric_name: str) -> dict[str, Any] | None:
    eligible = [result for result in results if result["metrics"].get(metric_name) is not None]
    if not eligible:
        return None
    best = max(eligible, key=lambda result: float(result["metrics"][metric_name]))
    return {
        "value": float(best["metrics"][metric_name]),
        "model_name": best["model_name"],
        "feature_set_name": best["feature_set_name"],
    }


def _collect_messages(experiments: list[dict[str, Any]], key: str) -> list[str]:
    messages: list[str] = []
    for result in experiments:
        for message in result.get(key, []):
            if message not in messages:
                messages.append(message)
    return messages


def _safe_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in value)
