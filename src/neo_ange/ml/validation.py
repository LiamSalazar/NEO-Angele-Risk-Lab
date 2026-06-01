"""Statistical validation reports for secondary ML evidence."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split

from neo_ange.ml.baselines import RANDOM_FOREST_MODEL, build_model_pipeline
from neo_ange.ml.dataset import MLDatasetLoader
from neo_ange.ml.feature_sets import FeatureSetRegistry
from neo_ange.utils.serialization import write_json


class MLValidationReportBuilder:
    """Build cross-validation and diagnostic reports for baseline ML."""

    def __init__(
        self,
        gold_root: str | Path = "data/gold",
        report_dir: str | Path = "reports/model_evidence",
        random_state: int = 42,
    ) -> None:
        self.gold_root = Path(gold_root)
        self.report_dir = Path(report_dir)
        self.random_state = random_state
        self.loader = MLDatasetLoader(self.gold_root)
        self.feature_sets = FeatureSetRegistry()

    def build(self, target: str = "pha") -> dict[str, Any]:
        """Write validation reports and return output paths."""
        self.report_dir.mkdir(parents=True, exist_ok=True)
        df = self.loader.prepare_training_frame(target=target)
        validation = self.loader.validate_target(df, target=target)
        if validation.get("status") != "ok":
            return self._write_insufficient(validation, target)
        features = self.feature_sets.resolve(df, "orbital_only", target=target)["features"]
        if not features:
            validation = {**validation, "warnings": ["No orbital_only features are available."]}
            return self._write_insufficient(validation, target)
        training = df.dropna(subset=[target]).copy()
        y = pd.to_numeric(training[target], errors="coerce").astype(int)
        X = training[features].copy()
        folds = _fold_count(y)
        if folds < 2:
            validation = {**validation, "warnings": ["Not enough class support for CV."]}
            return self._write_insufficient(validation, target)
        cv = StratifiedKFold(n_splits=folds, shuffle=True, random_state=self.random_state)
        model = build_model_pipeline(RANDOM_FOREST_MODEL, features, random_state=self.random_state)
        probabilities = cross_val_predict(model, X, y, cv=cv, method="predict_proba")[:, 1]
        predictions = (probabilities >= 0.5).astype(int)
        cv_metrics = _cross_validation_metrics(y, predictions, probabilities, folds)
        curve_outputs = self._write_curves(y, probabilities)
        calibration_outputs = self._write_calibration(y, probabilities)
        threshold_outputs = self._write_threshold_analysis(y, probabilities)
        permutation_outputs = self._write_permutation_importance(X, y, features)
        cv_csv = self.report_dir / "cross_validation_metrics.csv"
        pd.DataFrame([cv_metrics]).to_csv(cv_csv, index=False)
        cv_summary = {
            "status": "success",
            "target": target,
            "feature_set": "orbital_only",
            "model_name": RANDOM_FOREST_MODEL,
            "folds": folds,
            "metrics": cv_metrics,
            "leakage_notes": {
                "orbital_only": "low_leakage_risk",
                "full_features": "leakage_sensitive",
                "definition_features_only": "leakage_sensitive",
                "graph_node_features_with_risk_score": "leakage_sensitive",
            },
            "recommended_use": "secondary evidence only",
        }
        cv_summary_json = write_json(cv_summary, self.report_dir / "cross_validation_summary.json")
        cv_summary_md = self.report_dir / "cross_validation_summary.md"
        cv_summary_md.write_text(_render_cv_summary(cv_summary), encoding="utf-8")
        return {
            "status": "success",
            "outputs": {
                "cross_validation_metrics_csv": str(cv_csv),
                "cross_validation_summary_json": str(cv_summary_json),
                "cross_validation_summary_markdown": str(cv_summary_md),
                **curve_outputs,
                **calibration_outputs,
                **threshold_outputs,
                **permutation_outputs,
            },
            "metrics": cv_metrics,
        }

    def _write_insufficient(self, validation: dict[str, Any], target: str) -> dict[str, Any]:
        empty_csvs = [
            "cross_validation_metrics.csv",
            "roc_curve_points.csv",
            "pr_curve_points.csv",
            "calibration_curve_points.csv",
            "permutation_importance.csv",
            "threshold_analysis.csv",
        ]
        for filename in empty_csvs:
            pd.DataFrame().to_csv(self.report_dir / filename, index=False)
        summary = {
            "status": "insufficient_data",
            "target": target,
            "validation": validation,
            "recommended_use": "do not interpret ML metrics until data is sufficient",
        }
        outputs = {
            "cross_validation_summary_json": str(
                write_json(summary, self.report_dir / "cross_validation_summary.json")
            ),
            "calibration_summary_json": str(
                write_json(summary, self.report_dir / "calibration_summary.json")
            ),
            "threshold_analysis_summary_json": str(
                write_json(summary, self.report_dir / "threshold_analysis_summary.json")
            ),
        }
        (self.report_dir / "cross_validation_summary.md").write_text(
            "# Cross-Validation Summary\n\nInsufficient data for cross-validation.\n",
            encoding="utf-8",
        )
        (self.report_dir / "permutation_importance_summary.md").write_text(
            "# Permutation Importance\n\nInsufficient data for permutation importance.\n",
            encoding="utf-8",
        )
        return {"status": "insufficient_data", "outputs": outputs, "metrics": {}}

    def _write_curves(self, y: pd.Series, probabilities: np.ndarray) -> dict[str, str]:
        fpr, tpr, roc_thresholds = roc_curve(y, probabilities)
        precision, recall, pr_thresholds = precision_recall_curve(y, probabilities)
        roc_path = self.report_dir / "roc_curve_points.csv"
        pr_path = self.report_dir / "pr_curve_points.csv"
        pd.DataFrame(
            {
                "fpr": fpr,
                "tpr": tpr,
                "threshold": roc_thresholds,
            }
        ).to_csv(roc_path, index=False)
        pr_threshold_values = np.append(pr_thresholds, np.nan)
        pd.DataFrame(
            {
                "precision": precision,
                "recall": recall,
                "threshold": pr_threshold_values,
            }
        ).to_csv(pr_path, index=False)
        return {"roc_curve_points_csv": str(roc_path), "pr_curve_points_csv": str(pr_path)}

    def _write_calibration(self, y: pd.Series, probabilities: np.ndarray) -> dict[str, str]:
        bins = np.linspace(0.0, 1.0, 11)
        rows: list[dict[str, Any]] = []
        ece = 0.0
        for lower, upper in zip(bins[:-1], bins[1:], strict=False):
            mask = (probabilities >= lower) & (
                probabilities <= upper if upper == 1.0 else probabilities < upper
            )
            count = int(mask.sum())
            if not count:
                rows.append(
                    {
                        "bin_lower": lower,
                        "bin_upper": upper,
                        "count": 0,
                        "mean_predicted_probability": None,
                        "observed_positive_rate": None,
                    }
                )
                continue
            mean_prob = float(probabilities[mask].mean())
            observed = float(np.asarray(y)[mask].mean())
            ece += (count / len(y)) * abs(mean_prob - observed)
            rows.append(
                {
                    "bin_lower": lower,
                    "bin_upper": upper,
                    "count": count,
                    "mean_predicted_probability": mean_prob,
                    "observed_positive_rate": observed,
                }
            )
        curve_path = self.report_dir / "calibration_curve_points.csv"
        pd.DataFrame(rows).to_csv(curve_path, index=False)
        summary = {
            "status": "success",
            "brier_score": float(brier_score_loss(y, probabilities)),
            "expected_calibration_error": float(ece),
            "calibration_method": "out_of_fold_probability_bins",
        }
        summary_path = write_json(summary, self.report_dir / "calibration_summary.json")
        return {
            "calibration_curve_points_csv": str(curve_path),
            "calibration_summary_json": str(summary_path),
        }

    def _write_threshold_analysis(self, y: pd.Series, probabilities: np.ndarray) -> dict[str, str]:
        rows = []
        for threshold in np.arange(0.1, 1.0, 0.1):
            pred = (probabilities >= threshold).astype(int)
            tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
            rows.append(
                {
                    "threshold": round(float(threshold), 2),
                    "accuracy": float(accuracy_score(y, pred)),
                    "precision": float(precision_score(y, pred, zero_division=0)),
                    "recall": float(recall_score(y, pred, zero_division=0)),
                    "f1": float(f1_score(y, pred, zero_division=0)),
                    "false_negative_rate": float(fn / (fn + tp)) if (fn + tp) else None,
                    "true_positive": int(tp),
                    "false_positive": int(fp),
                    "true_negative": int(tn),
                    "false_negative": int(fn),
                }
            )
        df = pd.DataFrame(rows)
        csv_path = self.report_dir / "threshold_analysis.csv"
        df.to_csv(csv_path, index=False)
        summary = {
            "status": "success",
            "balanced_f1_threshold": _best_threshold(df, "f1"),
            "high_recall_threshold": _high_recall_threshold(df),
            "low_false_negative_threshold": _low_false_negative_threshold(df),
        }
        summary_path = write_json(summary, self.report_dir / "threshold_analysis_summary.json")
        return {
            "threshold_analysis_csv": str(csv_path),
            "threshold_analysis_summary_json": str(summary_path),
        }

    def _write_permutation_importance(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        features: list[str],
    ) -> dict[str, str]:
        stratify = y if y.value_counts().min() >= 2 else None
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.25,
            random_state=self.random_state,
            stratify=stratify,
        )
        model = build_model_pipeline(RANDOM_FOREST_MODEL, features, random_state=self.random_state)
        model.fit(X_train, y_train)
        importance = permutation_importance(
            model,
            X_test,
            y_test,
            n_repeats=10,
            random_state=self.random_state,
            scoring="average_precision",
        )
        rows = [
            {
                "feature": feature,
                "importance_mean": float(mean),
                "importance_std": float(std),
                "model_name": RANDOM_FOREST_MODEL,
                "feature_set": "orbital_only",
                "leakage_sensitive": False,
            }
            for feature, mean, std in zip(
                features,
                importance.importances_mean,
                importance.importances_std,
                strict=False,
            )
        ]
        rows.sort(key=lambda item: item["importance_mean"], reverse=True)
        csv_path = self.report_dir / "permutation_importance.csv"
        pd.DataFrame(rows).to_csv(csv_path, index=False)
        md_path = self.report_dir / "permutation_importance_summary.md"
        md_path.write_text(_render_permutation_summary(rows), encoding="utf-8")
        return {
            "permutation_importance_csv": str(csv_path),
            "permutation_importance_summary_markdown": str(md_path),
        }


def _cross_validation_metrics(
    y: pd.Series,
    predictions: np.ndarray,
    probabilities: np.ndarray,
    folds: int,
) -> dict[str, Any]:
    tn, fp, fn, tp = confusion_matrix(y, predictions, labels=[0, 1]).ravel()
    return {
        "folds": folds,
        "n_samples": int(len(y)),
        "accuracy_mean": float(accuracy_score(y, predictions)),
        "accuracy_std": None,
        "precision_mean": float(precision_score(y, predictions, zero_division=0)),
        "precision_std": None,
        "recall_mean": float(recall_score(y, predictions, zero_division=0)),
        "recall_std": None,
        "f1_mean": float(f1_score(y, predictions, zero_division=0)),
        "f1_std": None,
        "roc_auc_mean": float(roc_auc_score(y, probabilities)),
        "roc_auc_std": None,
        "pr_auc_mean": float(average_precision_score(y, probabilities)),
        "pr_auc_std": None,
        "false_negative_rate_mean": float(fn / (fn + tp)) if (fn + tp) else None,
        "false_negative_rate_std": None,
        "brier_score": float(brier_score_loss(y, probabilities)),
    }


def _fold_count(y: pd.Series) -> int:
    class_counts = y.value_counts()
    if class_counts.empty:
        return 0
    return int(min(5, class_counts.min()))


def _best_threshold(df: pd.DataFrame, metric: str) -> float | None:
    if df.empty or metric not in df.columns:
        return None
    row = df.sort_values(metric, ascending=False).iloc[0]
    return float(row["threshold"])


def _high_recall_threshold(df: pd.DataFrame) -> float | None:
    if df.empty:
        return None
    candidates = df[df["recall"] >= 0.90]
    if candidates.empty:
        candidates = df.sort_values("recall", ascending=False).head(1)
    row = candidates.sort_values(["false_negative_rate", "threshold"]).iloc[0]
    return float(row["threshold"])


def _low_false_negative_threshold(df: pd.DataFrame) -> float | None:
    if df.empty:
        return None
    row = df.sort_values(["false_negative_rate", "precision"], ascending=[True, False]).iloc[0]
    return float(row["threshold"])


def _render_cv_summary(summary: dict[str, Any]) -> str:
    metrics = summary.get("metrics", {})
    lines = [
        "# Cross-Validation Summary",
        "",
        "Out-of-fold validation for secondary ML evidence. Ranking remains based on the "
        "deterministic Risk Priority Score.",
        "",
        f"- Status: {summary.get('status')}",
        f"- Model: {summary.get('model_name')}",
        f"- Feature set: {summary.get('feature_set')}",
        f"- Folds: {summary.get('folds')}",
        f"- PR-AUC: {metrics.get('pr_auc_mean')}",
        f"- ROC-AUC: {metrics.get('roc_auc_mean')}",
        f"- F1: {metrics.get('f1_mean')}",
        f"- False negative rate: {metrics.get('false_negative_rate_mean')}",
        "",
        "Leakage-sensitive feature sets remain marked as secondary or diagnostic only.",
        "",
    ]
    return "\n".join(lines)


def _render_permutation_summary(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Permutation Importance",
        "",
        "Permutation importance is computed for the orbital_only random forest baseline on a "
        "held-out split using average precision scoring.",
        "",
    ]
    for row in rows[:10]:
        lines.append(
            f"- {row['feature']}: mean={row['importance_mean']}, std={row['importance_std']}"
        )
    lines.append("")
    return "\n".join(lines)
