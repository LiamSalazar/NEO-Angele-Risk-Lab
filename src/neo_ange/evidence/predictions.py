"""Prediction generation for model evidence artifacts."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from neo_ange.evidence.model_cards import leakage_risk_for_feature_set
from neo_ange.evidence.schemas import PredictionRecord
from neo_ange.ml.baselines import build_model_pipeline
from neo_ange.ml.feature_sets import FeatureSetRegistry
from neo_ange.ml.metrics import calculate_classification_metrics

EVIDENCE_EXPERIMENTS = [
    ("random_forest", "no_definition_features"),
    ("logistic_regression", "orbital_only"),
    ("random_forest", "orbital_only"),
    ("random_forest", "full_features"),
    ("random_forest", "definition_features_only"),
]


def run_tabular_predictions(
    df: pd.DataFrame,
    target: str = "pha",
    random_state: int = 42,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Return eval predictions, full-dataset inference rows, and metric records."""
    if df.empty or target not in df.columns:
        return [], [], []
    frame = df.copy()
    y = _target_to_int(frame[target])
    frame = frame.loc[y.notna()].copy()
    y = y.loc[frame.index].astype(int)
    if len(frame) < 20 or y.nunique() < 2:
        return [], [], []

    train_idx, test_idx = train_test_split(
        frame.index,
        test_size=0.25,
        random_state=random_state,
        stratify=y,
    )
    registry = FeatureSetRegistry()
    eval_prediction_rows: list[dict[str, Any]] = []
    full_prediction_rows: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    for model_name, feature_set in EVIDENCE_EXPERIMENTS:
        resolved = registry.resolve(frame, feature_set, target=target)
        features = resolved["features"]
        if not features:
            metric_rows.append(
                {
                    "status": "skipped",
                    "model_name": model_name,
                    "model_family": "tabular",
                    "feature_set": feature_set,
                    "target": target,
                    "metrics": {},
                    "warnings": resolved["warnings"],
                }
            )
            continue
        eval_model = build_model_pipeline(model_name, features, random_state=random_state)
        X_train = frame.loc[train_idx, features]
        X_test = frame.loc[test_idx, features]
        y_train = y.loc[train_idx]
        y_test = y.loc[test_idx]
        eval_model.fit(X_train, y_train)
        eval_predicted = eval_model.predict(X_test)
        eval_probabilities = _positive_probability(eval_model, X_test)
        metrics = calculate_classification_metrics(y_test, eval_predicted, eval_probabilities)
        metric_rows.append(
            {
                "status": "success",
                "model_name": model_name,
                "model_family": "tabular",
                "feature_set": feature_set,
                "target": target,
                "metrics": metrics,
                "warnings": [*resolved["warnings"], *metrics.get("warnings", [])],
            }
        )
        eval_prediction_rows.extend(
            _prediction_rows(
                frame.loc[test_idx],
                y_test,
                eval_predicted,
                eval_probabilities,
                model_name=model_name,
                feature_set=feature_set,
                model_family="tabular",
                prediction_mode="eval",
                training_strategy="holdout_train_test_split",
            )
        )

        full_model = build_model_pipeline(model_name, features, random_state=random_state)
        full_model.fit(frame.loc[:, features], y)
        full_predicted = full_model.predict(frame.loc[:, features])
        full_probabilities = _positive_probability(full_model, frame.loc[:, features])
        full_prediction_rows.extend(
            _prediction_rows(
                frame,
                y,
                full_predicted,
                full_probabilities,
                model_name=model_name,
                feature_set=feature_set,
                model_family="tabular",
                prediction_mode="full",
                training_strategy="full_labeled_dataset_after_holdout_evaluation",
            )
        )
    return eval_prediction_rows, full_prediction_rows, metric_rows


def _prediction_rows(
    frame: pd.DataFrame,
    y_true: pd.Series,
    predicted: Any,
    probabilities: Any,
    *,
    model_name: str,
    feature_set: str,
    model_family: str,
    prediction_mode: str,
    training_strategy: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    leakage_risk = leakage_risk_for_feature_set(feature_set)
    evidence_role = "diagnostic" if leakage_risk == "high" else "secondary_evidence"
    for (_, source), actual, label, probability in zip(
        frame.iterrows(), y_true.to_numpy(), predicted, probabilities, strict=True
    ):
        row = PredictionRecord(
            object_key=str(source.get("object_key")),
            designation=_designation(source),
            actual_label=int(actual),
            predicted_label=int(label),
            predicted_probability=float(probability),
            model_name=model_name,
            feature_set=feature_set,
            model_family=model_family,
            correct=bool(int(actual) == int(label)),
            confidence_bucket=confidence_bucket(float(probability)),
            risk_score_0_100=_optional_float(source.get("risk_score_0_100")),
            risk_category=_optional_str(source.get("risk_category")),
            notes=_prediction_note(feature_set),
        ).to_dict()
        row.update(
            {
                "prediction_mode": prediction_mode,
                "training_strategy": training_strategy,
                "leakage_risk": leakage_risk,
                "evidence_role": evidence_role,
            }
        )
        rows.append(row)
    return rows


def add_graph_metric_records(
    gnn_metrics: pd.DataFrame,
    target: str = "pha",
) -> list[dict[str, Any]]:
    """Normalize graph/GNN metrics CSV rows as evidence metric records."""
    if gnn_metrics.empty:
        return []
    rows = []
    for _, row in gnn_metrics.iterrows():
        feature_set = str(row.get("feature_set") or "graph")
        model_name = str(row.get("model_name") or row.get("model") or "graph_model")
        family = str(row.get("family") or "graph")
        model_family = "gnn" if family == "gnn" else "graph"
        if family == "baseline" and feature_set != "graph_node_features":
            model_family = "tabular"
        metrics = {
            key: _optional_float(row.get(key))
            for key in [
                "accuracy",
                "precision",
                "recall",
                "f1",
                "roc_auc",
                "pr_auc",
                "false_negative_rate",
            ]
        }
        rows.append(
            {
                "status": str(row.get("status") or "unknown"),
                "model_name": model_name,
                "model_family": model_family,
                "feature_set": feature_set,
                "target": str(row.get("target") or target),
                "metrics": metrics,
                "warnings": [],
            }
        )
    return rows


def confidence_bucket(probability: float) -> str:
    """Bucket positive-class probability for frontend filtering."""
    confidence = max(probability, 1 - probability)
    if confidence >= 0.85:
        return "high"
    if confidence >= 0.65:
        return "medium"
    return "low"


def _target_to_int(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.astype("Int64")
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce").astype("Int64")
    normalized = series.astype("string").str.lower()
    return normalized.map({"true": 1, "1": 1, "yes": 1, "false": 0, "0": 0, "no": 0}).astype(
        "Int64"
    )


def _positive_probability(model: Any, X_test: pd.DataFrame) -> np.ndarray:
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(X_test)
        array = np.asarray(probabilities)
        if array.ndim == 2 and array.shape[1] >= 2:
            return array[:, 1].astype(float)
        return array.astype(float)
    predicted = np.asarray(model.predict(X_test)).astype(float)
    return predicted


def _designation(row: pd.Series) -> str | None:
    for key in ["des", "name", "full_name", "object_key"]:
        value = row.get(key)
        if value is not None and not pd.isna(value):
            return str(value)
    return None


def _optional_float(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(result):
        return None
    return result


def _optional_str(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    return str(value)


def _prediction_note(feature_set: str) -> str:
    if feature_set in {"full_features", "definition_features_only"}:
        return "Leakage-sensitive diagnostic; not preferred for user-facing evidence."
    return "Defensible secondary evidence view."
