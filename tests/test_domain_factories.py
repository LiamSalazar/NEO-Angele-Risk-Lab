from __future__ import annotations

import numpy as np
import pandas as pd

from neo_ange.domain.factories import AsteroidFactory


def test_factory_from_gold_row_handles_missing_values() -> None:
    asteroid = AsteroidFactory.from_gold_row(
        {
            "object_key": "100",
            "spkid": np.nan,
            "des": "2026 AA",
            "e": 0.1,
            "a": 1.2,
            "q": 0.9,
            "i": 1.0,
            "diameter": np.nan,
            "h": 22.0,
            "pha": "false",
        }
    )

    assert asteroid.object_key() == "100"
    assert asteroid.identity.spkid is None
    assert asteroid.physical.h == 22.0
    assert asteroid.pha is False


def test_factory_from_risk_row_and_many_from_dataframe() -> None:
    df = pd.DataFrame(
        [
            {
                "object_key": "100",
                "e": 0.1,
                "a": 1.0,
                "q": 0.9,
                "i": 2.0,
                "risk_score_0_100": 55,
                "risk_category": "medium",
            }
        ]
    )

    asteroid, score = AsteroidFactory.from_risk_row(df.iloc[0])

    assert asteroid.object_key() == "100"
    assert score is not None
    assert score.object_key == "100"
    assert score.risk_score_0_100 == 55
    assert len(AsteroidFactory.many_from_dataframe(df)) == 1
