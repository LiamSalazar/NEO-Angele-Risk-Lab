from __future__ import annotations

from neo_ange.domain.approach import CloseApproachSummary
from neo_ange.domain.asteroid import Asteroid
from neo_ange.domain.graph import OrbitalGraph, OrbitalGraphNode, OrbitalSimilarityEdge
from neo_ange.domain.identity import AsteroidIdentity
from neo_ange.domain.orbit import Orbit
from neo_ange.domain.physical import PhysicalProperties
from neo_ange.domain.risk import RiskScore
from neo_ange.domain.sentry import SentryRiskSignal
from neo_ange.domain.simulation import MonteCarloResult


def test_domain_entities_expose_behavior() -> None:
    identity = AsteroidIdentity(object_key="100", spkid="100", name="Test")
    orbit = Orbit(e=0.1, a=1.2, q=0.9, i=3.0, moid=0.02, condition_code="3")
    physical = PhysicalProperties(h=21.0, diameter=0.3)
    approach = CloseApproachSummary(min_close_approach_dist=0.01, max_close_approach_v_rel=20)
    sentry = SentryRiskSignal(sentry_flag=True, sentry_ip=1e-6)
    asteroid = Asteroid(identity, orbit, physical, approach, sentry, neo=True, pha=False)

    assert identity.best_identifier() == "100"
    assert orbit.has_minimum_orbital_data()
    assert len(orbit.orbital_vector()) == 12
    assert physical.size_indicator() is not None
    assert sentry.has_sentry_signal()
    assert asteroid.to_feature_dict()["object_key"] == "100"


def test_score_simulation_and_graph_entities() -> None:
    score = RiskScore(
        object_key="100",
        risk_score_0_100=42.0,
        orbital_risk_component=0.9,
        physical_risk_component=0.2,
        sentry_risk_component=0.4,
    )
    assert score.dominant_components(2)[0]["component"] == "orbital_risk_component"

    result = MonteCarloResult(
        object_key="100",
        base_score=40,
        mean_score=41,
        std_score=2,
        p95_score=45,
        category_shift_probability=0.02,
    )
    assert result.stability_summary()["stability"] == "stable"

    graph = OrbitalGraph(
        nodes=[
            OrbitalGraphNode(node_id=0, object_key="a"),
            OrbitalGraphNode(node_id=1, object_key="b"),
        ],
        edges=[OrbitalSimilarityEdge(source=0, target=1, similarity=0.8, distance=0.2)],
    )
    assert graph.node_count() == 2
    assert graph.edge_count() == 1
    assert graph.density() == 1.0
