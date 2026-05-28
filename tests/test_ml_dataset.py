from __future__ import annotations

import pandas as pd

from neo_ange.ml.dataset import MLDatasetLoader


def test_load_gold_features_and_prepare_training_frame(tmp_path) -> None:
    gold = tmp_path / "gold" / "neo_risk_features"
    gold.mkdir(parents=True)
    pd.DataFrame({"object_key": ["a", "b"], "pha": [True, False], "h": [20.0, 23.0]}).to_parquet(
        gold / "part.parquet"
    )
    loader = MLDatasetLoader(tmp_path / "gold")

    df = loader.load_gold_features()
    validation = loader.validate_target(df)
    training = loader.prepare_training_frame()

    assert len(df) == 2
    assert validation["status"] == "ok"
    assert validation["n_positive"] == 1
    assert training["pha"].tolist() == [1, 0]


def test_validate_target_missing_and_single_class() -> None:
    loader = MLDatasetLoader()

    missing = loader.validate_target(pd.DataFrame({"h": [1.0]}))
    single = loader.validate_target(pd.DataFrame({"pha": [True, True]}))

    assert missing["status"] == "missing_target"
    assert single["status"] == "single_class"
