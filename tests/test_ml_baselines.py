from __future__ import annotations

import pandas as pd

from neo_ange.ml.baselines import (
    DUMMY_MODEL,
    LOGISTIC_MODEL,
    RANDOM_FOREST_MODEL,
    RuleBasedPHABaseline,
    build_model_pipeline,
)


def _training_data() -> tuple[pd.DataFrame, pd.Series]:
    X = pd.DataFrame(
        {
            "h": [19, 20, 21, 22, 23, 24, 25, 26],
            "moid": [0.01, 0.02, 0.03, 0.04, 0.2, 0.3, 0.4, 0.5],
            "e": [0.1, 0.2, 0.2, 0.3, 0.4, 0.4, 0.5, 0.6],
        }
    )
    y = pd.Series([1, 1, 1, 1, 0, 0, 0, 0])
    return X, y


def test_dummy_logistic_and_random_forest_train() -> None:
    X, y = _training_data()

    for model_name in [DUMMY_MODEL, LOGISTIC_MODEL, RANDOM_FOREST_MODEL]:
        model = build_model_pipeline(model_name, ["h", "moid", "e"])
        model.fit(X, y)
        predictions = model.predict(X)
        assert len(predictions) == len(y)


def test_rule_based_pha_predicts_definition_and_handles_nulls() -> None:
    model = RuleBasedPHABaseline()
    X = pd.DataFrame({"h": [21.0, 23.0, None], "moid": [0.04, 0.04, 0.01]})

    assert model.predict(X).tolist() == [1, 0, 0]
    assert model.predict_proba(X).shape == (3, 2)
