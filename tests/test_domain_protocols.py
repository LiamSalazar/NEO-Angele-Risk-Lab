from __future__ import annotations

from typing import Any

from neo_ange.domain.approach import CloseApproach, CloseApproachHistory
from neo_ange.domain.asteroid import Asteroid
from neo_ange.domain.identity import AsteroidIdentity
from neo_ange.domain.orbit import Orbit
from neo_ange.domain.physical import PhysicalProperties
from neo_ange.domain.protocols import (
    FeatureExportable,
    IdentifiableDomainObject,
    RiskScoringStrategy,
    SerializableDomainObject,
    SimulationStrategy,
    Summarizable,
)


class ToyScorer:
    def score_row(self, row: dict[str, Any]) -> dict[str, Any]:
        return {**row, "risk_score_0_100": 42.0}

    def score_dataframe(self, df: Any) -> Any:
        return df


class ToySimulation:
    def simulate_object(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return {"args": args, "kwargs": kwargs}


def test_domain_protocols_accept_structural_domain_objects() -> None:
    asteroid = Asteroid(
        identity=AsteroidIdentity(object_key="100", name="Protocol NEO"),
        orbit=Orbit(e=0.1, a=1.0, q=0.8, i=2.0),
        physical=PhysicalProperties(h=21.0),
    )
    history = CloseApproachHistory((CloseApproach(dist=0.02, v_rel=20),))

    assert isinstance(asteroid, SerializableDomainObject)
    assert isinstance(asteroid, FeatureExportable)
    assert isinstance(asteroid, IdentifiableDomainObject)
    assert isinstance(history, SerializableDomainObject)
    assert isinstance(history, Summarizable)
    assert isinstance(ToyScorer(), RiskScoringStrategy)
    assert isinstance(ToySimulation(), SimulationStrategy)
