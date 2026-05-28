"""Baseline classifiers for the first ML laboratory phase."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from neo_ange.ml.preprocessing import build_linear_preprocessor, build_tree_preprocessor

DUMMY_MODEL = "dummy_most_frequent"
LOGISTIC_MODEL = "logistic_regression"
RANDOM_FOREST_MODEL = "random_forest"
HIST_GRADIENT_BOOSTING_MODEL = "hist_gradient_boosting"
RULE_BASED_PHA_MODEL = "rule_based_pha"


class RuleBasedPHABaseline:
    """Approximate PHA definition baseline using MOID and absolute magnitude H."""

    def fit(self, X: pd.DataFrame, y: Any = None) -> RuleBasedPHABaseline:
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        frame = _as_frame(X)
        h = _numeric_series(frame, "h")
        moid = _numeric_series(frame, "moid")
        positive = (moid <= 0.05) & (h <= 22.0) & moid.notna() & h.notna()
        return positive.astype(int).to_numpy()

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        predictions = self.predict(X)
        return np.column_stack([1 - predictions, predictions]).astype(float)


def build_estimator(model_name: str, random_state: int = 42) -> Any:
    """Build an unfitted baseline estimator by name."""
    if model_name == DUMMY_MODEL:
        return DummyClassifier(strategy="most_frequent")
    if model_name == LOGISTIC_MODEL:
        return LogisticRegression(class_weight="balanced", max_iter=1000, random_state=random_state)
    if model_name == RANDOM_FOREST_MODEL:
        return RandomForestClassifier(
            class_weight="balanced",
            n_estimators=100,
            min_samples_leaf=2,
            random_state=random_state,
            n_jobs=-1,
        )
    if model_name == HIST_GRADIENT_BOOSTING_MODEL:
        return HistGradientBoostingClassifier(
            learning_rate=0.08,
            max_iter=100,
            random_state=random_state,
        )
    if model_name == RULE_BASED_PHA_MODEL:
        return RuleBasedPHABaseline()
    allowed = ", ".join(default_model_names(include_hist_gradient=True, include_rule_based=True))
    raise ValueError(f"Unknown baseline model '{model_name}'. Expected one of: {allowed}.")


def build_model_pipeline(
    model_name: str,
    feature_names: list[str],
    random_state: int = 42,
) -> Pipeline | RuleBasedPHABaseline:
    """Build a preprocessing-plus-model pipeline where appropriate."""
    estimator = build_estimator(model_name, random_state=random_state)
    if model_name == RULE_BASED_PHA_MODEL:
        return estimator
    if model_name == LOGISTIC_MODEL:
        preprocessor = build_linear_preprocessor(feature_names)
    else:
        preprocessor = build_tree_preprocessor(feature_names)
    return Pipeline(steps=[("preprocessor", preprocessor), ("model", estimator)])


def default_model_names(
    include_hist_gradient: bool = False,
    include_rule_based: bool = False,
) -> list[str]:
    """Return the default baseline model list."""
    names = [DUMMY_MODEL, LOGISTIC_MODEL, RANDOM_FOREST_MODEL]
    if include_hist_gradient:
        names.append(HIST_GRADIENT_BOOSTING_MODEL)
    if include_rule_based:
        names.append(RULE_BASED_PHA_MODEL)
    return names


def _as_frame(X: Any) -> pd.DataFrame:
    if isinstance(X, pd.DataFrame):
        return X
    return pd.DataFrame(X)


def _numeric_series(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(np.nan, index=frame.index)
    return pd.to_numeric(frame[column], errors="coerce")
