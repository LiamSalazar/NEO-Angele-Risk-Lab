"""Baseline model runners for graph research comparison."""

from __future__ import annotations

import warnings as warning_lib
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.semi_supervised import LabelPropagation

from neo_ange.gnn.evaluation import evaluate_binary_classification
from neo_ange.gnn.schemas import FORBIDDEN_GRAPH_FEATURES, GRAPH_NODE_FEATURES
from neo_ange.ml.feature_sets import FeatureSetRegistry
from neo_ange.utils.serialization import to_jsonable


class GraphBaselineRunner:
    """Run leakage-aware tabular and graph-feature baselines."""

    def __init__(self, random_state: int = 42) -> None:
        self.random_state = random_state
        self.feature_registry = FeatureSetRegistry()

    def run_all(
        self,
        df: pd.DataFrame,
        target: str = "pha",
        feature_sets: list[str] | None = None,
    ) -> dict[str, Any]:
        """Run baseline models across selected feature sets."""
        feature_sets = feature_sets or [
            "no_definition_features",
            "orbital_only",
            "graph_node_features",
        ]
        results: dict[str, Any] = {}
        for feature_set in feature_sets:
            results[feature_set] = {
                "logistic_regression": self.run_logistic_regression_baseline(
                    df, target=target, feature_set=feature_set
                ),
                "random_forest": self.run_random_forest_baseline(
                    df, target=target, feature_set=feature_set
                ),
                "mlp": self.run_mlp_baseline(df, target=target, feature_set=feature_set),
                "label_propagation": self.run_label_propagation_baseline(
                    df, target=target, feature_set=feature_set
                ),
            }
        return to_jsonable(results)

    def run_logistic_regression_baseline(
        self,
        df: pd.DataFrame,
        target: str = "pha",
        feature_set: str = "no_definition_features",
    ) -> dict[str, Any]:
        """Run a logistic regression tabular baseline."""
        model = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("model", LogisticRegression(max_iter=1000, random_state=self.random_state)),
            ]
        )
        return self._fit_evaluate(df, model, target=target, feature_set=feature_set)

    def run_random_forest_baseline(
        self,
        df: pd.DataFrame,
        target: str = "pha",
        feature_set: str = "no_definition_features",
    ) -> dict[str, Any]:
        """Run a random forest tabular baseline."""
        model = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=100,
                        min_samples_leaf=2,
                        random_state=self.random_state,
                        n_jobs=1,
                    ),
                ),
            ]
        )
        return self._fit_evaluate(df, model, target=target, feature_set=feature_set)

    def run_mlp_baseline(
        self,
        df: pd.DataFrame,
        target: str = "pha",
        feature_set: str = "no_definition_features",
    ) -> dict[str, Any]:
        """Run a small MLP tabular baseline."""
        model = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                (
                    "model",
                    MLPClassifier(
                        hidden_layer_sizes=(32,),
                        max_iter=200,
                        random_state=self.random_state,
                        early_stopping=False,
                    ),
                ),
            ]
        )
        return self._fit_evaluate(df, model, target=target, feature_set=feature_set)

    def run_label_propagation_baseline(
        self,
        df: pd.DataFrame,
        target: str = "pha",
        feature_set: str = "graph_node_features",
    ) -> dict[str, Any]:
        """Run a lightweight label propagation baseline over selected features."""
        prepared = self._prepare_xy(df, target=target, feature_set=feature_set)
        if prepared["status"] != "success":
            return prepared
        x = prepared["x"]
        y = prepared["y"]
        split = self._split(x, y)
        if split["status"] != "success":
            return split
        y_train_partial = np.full_like(y, fill_value=-1)
        y_train_partial[split["train_idx"]] = y[split["train_idx"]]
        try:
            model = Pipeline(
                [
                    ("imputer", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler()),
                    ("model", LabelPropagation(max_iter=1000)),
                ]
            )
            with warning_lib.catch_warnings(record=True) as caught:
                warning_lib.simplefilter("always", UserWarning)
                warning_lib.simplefilter("always", RuntimeWarning)
                model.fit(x, y_train_partial)
                y_pred = model.predict(x[split["test_idx"]])
                proba = _predict_proba(model, x[split["test_idx"]])
        except Exception as exc:
            return {
                "status": "failed",
                "feature_set": feature_set,
                "warnings": [f"Label propagation failed: {exc}"],
            }
        metrics = evaluate_binary_classification(y[split["test_idx"]], y_pred, proba)
        return {
            "status": "success",
            "feature_set": feature_set,
            "features": prepared["features"],
            "metrics": metrics,
            "warnings": [*prepared["warnings"], *[str(item.message) for item in caught]],
        }

    def _fit_evaluate(
        self,
        df: pd.DataFrame,
        model: Pipeline,
        target: str,
        feature_set: str,
    ) -> dict[str, Any]:
        prepared = self._prepare_xy(df, target=target, feature_set=feature_set)
        if prepared["status"] != "success":
            return prepared
        split = self._split(prepared["x"], prepared["y"])
        if split["status"] != "success":
            return split
        try:
            with warning_lib.catch_warnings(record=True) as caught:
                warning_lib.simplefilter("always", UserWarning)
                warning_lib.simplefilter("always", RuntimeWarning)
                warning_lib.simplefilter("always", ConvergenceWarning)
                model.fit(
                    prepared["x"][split["train_idx"]],
                    prepared["y"][split["train_idx"]],
                )
                y_pred = model.predict(prepared["x"][split["test_idx"]])
                proba = _predict_proba(model, prepared["x"][split["test_idx"]])
        except Exception as exc:
            return {
                "status": "failed",
                "feature_set": feature_set,
                "warnings": [f"Baseline training failed: {exc}"],
            }
        metrics = evaluate_binary_classification(prepared["y"][split["test_idx"]], y_pred, proba)
        return {
            "status": "success",
            "feature_set": feature_set,
            "features": prepared["features"],
            "metrics": metrics,
            "warnings": [*prepared["warnings"], *[str(item.message) for item in caught]],
        }

    def _prepare_xy(
        self,
        df: pd.DataFrame,
        target: str,
        feature_set: str,
    ) -> dict[str, Any]:
        if df.empty:
            return {"status": "insufficient_data", "warnings": ["Input dataframe is empty."]}
        if target not in df.columns:
            return {
                "status": "insufficient_data",
                "warnings": [f"Target '{target}' is not available."],
            }
        features, warnings = self._resolve_features(df, feature_set=feature_set, target=target)
        if not features:
            return {
                "status": "insufficient_data",
                "feature_set": feature_set,
                "warnings": [*warnings, "No usable features are available."],
            }
        y = _target_to_int(df[target])
        valid = y >= 0
        if int(valid.sum()) < 4:
            return {
                "status": "insufficient_data",
                "feature_set": feature_set,
                "warnings": [*warnings, "Need at least four labeled rows for baseline split."],
            }
        if len(np.unique(y[valid])) < 2:
            return {
                "status": "insufficient_data",
                "feature_set": feature_set,
                "warnings": [
                    *warnings,
                    "Target has a single class; supervised metrics are limited.",
                ],
            }
        numeric = df.loc[valid, features].apply(pd.to_numeric, errors="coerce")
        usable_features = [column for column in numeric.columns if not numeric[column].isna().all()]
        dropped = sorted(set(features) - set(usable_features))
        if dropped:
            warnings.append(f"Dropped all-missing features: {', '.join(dropped)}.")
        if not usable_features:
            return {
                "status": "insufficient_data",
                "feature_set": feature_set,
                "warnings": [*warnings, "No non-empty numeric features are available."],
            }
        x = numeric[usable_features].to_numpy(dtype=float)
        return {
            "status": "success",
            "x": x,
            "y": y[valid],
            "features": usable_features,
            "warnings": warnings,
        }

    def _resolve_features(
        self,
        df: pd.DataFrame,
        feature_set: str,
        target: str,
    ) -> tuple[list[str], list[str]]:
        if feature_set == "graph_node_features":
            features = [
                feature
                for feature in GRAPH_NODE_FEATURES
                if feature in df.columns and feature not in FORBIDDEN_GRAPH_FEATURES | {target}
            ]
            return features, []
        try:
            resolved = self.feature_registry.resolve(df, feature_set, target=target)
        except ValueError as exc:
            return [], [str(exc)]
        return resolved["features"], resolved["warnings"]

    def _split(self, x: np.ndarray, y: np.ndarray) -> dict[str, Any]:
        stratify = y if _can_stratify(y) else None
        try:
            train_idx, test_idx = train_test_split(
                np.arange(len(y)),
                test_size=0.3,
                random_state=self.random_state,
                stratify=stratify,
            )
        except ValueError as exc:
            return {"status": "insufficient_data", "warnings": [str(exc)]}
        if len(np.unique(y[train_idx])) < 2 or len(test_idx) == 0:
            return {
                "status": "insufficient_data",
                "warnings": ["Train/test split does not contain enough class diversity."],
            }
        return {"status": "success", "train_idx": train_idx, "test_idx": test_idx}


def _target_to_int(series: pd.Series) -> np.ndarray:
    normalized = series.astype("string").str.lower()
    y = np.full(len(series), fill_value=-1, dtype=int)
    y[normalized.isin(["true", "t", "1", "yes", "y"])] = 1
    y[normalized.isin(["false", "f", "0", "no", "n"])] = 0
    return y


def _can_stratify(y: np.ndarray) -> bool:
    unique, counts = np.unique(y, return_counts=True)
    return len(unique) > 1 and bool(np.all(counts >= 2))


def _predict_proba(model: Pipeline, x: np.ndarray) -> np.ndarray | None:
    if hasattr(model, "predict_proba"):
        try:
            proba = model.predict_proba(x)
        except Exception:
            return None
        if not np.isfinite(proba).all():
            return None
        return proba
    return None
