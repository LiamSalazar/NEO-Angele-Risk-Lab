from __future__ import annotations

from neo_ange.domain.approach import CloseApproach, CloseApproachHistory, CloseApproachSummary
from neo_ange.domain.asteroid import Asteroid
from neo_ange.domain.factories import AsteroidFactory
from neo_ange.domain.identity import AsteroidIdentity
from neo_ange.domain.orbit import Orbit, OrbitalElements
from neo_ange.domain.physical import PhysicalProperties
from neo_ange.domain.sentry import SentryRiskSignal


def test_asteroid_delegates_identity_behavior() -> None:
    asteroid = Asteroid(
        identity=AsteroidIdentity(object_key="neo-1", spkid="123", name="Angele"),
        orbit=Orbit(),
        physical=PhysicalProperties(),
    )

    assert asteroid.object_key() == "neo-1"
    assert asteroid.display_name() == "Angele"


def test_asteroid_identity_prioritizes_stable_identifier_and_display_name() -> None:
    identity = AsteroidIdentity(
        object_key="key-1",
        spkid="123",
        des="2026 AA",
        full_name="(2026 AA)",
        name="Test Object",
    )

    assert identity.best_identifier() == "key-1"
    assert identity.display_name() == "Test Object"
    assert AsteroidIdentity(des="2026 AA").best_identifier() == "2026 AA"
    assert AsteroidIdentity().display_name() == "Unknown object"


def test_orbit_encapsulates_vectors_proximity_and_uncertainty() -> None:
    close_orbit = Orbit(
        e=0.2,
        a=1.1,
        q=0.9,
        i=3.0,
        moid=0.01,
        condition_code="7",
        rms=1.0,
        arc_length=10,
        n_obs_used=5,
    )
    far_orbit = Orbit(e=0.2, a=1.1, q=0.9, i=3.0, moid=0.50)

    assert OrbitalElements is Orbit
    assert close_orbit.has_minimum_orbital_data()
    assert len(close_orbit.orbital_vector()) == 12
    assert close_orbit.proximity_indicator() > far_orbit.proximity_indicator()
    assert close_orbit.uncertainty_indicator() is not None
    assert not Orbit(e=0.2, a=1.1).has_minimum_orbital_data()


def test_physical_properties_encapsulate_size_signals() -> None:
    measured = PhysicalProperties(diameter=1.0, h=18.0)
    proxy = PhysicalProperties(h=28.0)

    assert measured.has_size_information()
    assert measured.size_indicator() > proxy.size_indicator()
    assert PhysicalProperties().size_indicator() is None


def test_sentry_signal_encapsulates_sentry_priority() -> None:
    sentry = SentryRiskSignal(
        sentry_flag=True,
        sentry_ip=1e-5,
        sentry_ps_cum=-3.0,
        sentry_ts_max=2,
        sentry_n_imp=3,
    )

    assert sentry.has_sentry_signal()
    assert sentry.sentry_priority_indicator() is not None
    assert not SentryRiskSignal(sentry_flag=False).has_sentry_signal()


def test_asteroid_risk_relevance_and_feature_dict_are_backward_compatible() -> None:
    history = CloseApproachHistory(
        (CloseApproach(close_approach_datetime="2030-Jan-01 00:00", dist=0.02, v_rel=20),)
    )
    summary = history.summarize()
    asteroid = Asteroid(
        identity=AsteroidIdentity(object_key="100", name="Test"),
        orbit=Orbit(e=0.1, a=1.2, q=0.9, i=1.0, moid=0.02),
        physical=PhysicalProperties(h=21.0),
        close_approach_summary=summary,
        sentry_signal=SentryRiskSignal(sentry_flag=True, sentry_ip=1e-6),
        neo=True,
        pha=False,
        close_approach_history=history,
    )

    features = asteroid.to_feature_dict()

    assert asteroid.has_risk_relevant_data()
    assert features["object_key"] == "100"
    assert features["min_close_approach_dist"] == 0.02
    assert features["max_close_approach_v_rel"] == 20.0
    assert features["close_approach_count"] == 1
    assert "close_approach_history" not in features
    assert asteroid.to_dict()["close_approach_history"]["close_approach_count"] == 1


def test_asteroid_recognizes_close_approach_history_as_risk_relevant_data() -> None:
    asteroid = Asteroid(
        identity=AsteroidIdentity(object_key="history-only"),
        orbit=Orbit(),
        physical=PhysicalProperties(),
        close_approach_history=CloseApproachHistory(
            (CloseApproach(close_approach_datetime="2030-Jan-01 00:00", dist=0.02),)
        ),
    )

    assert asteroid.has_risk_relevant_data()
    assert asteroid.close_approach_summary is None
    assert asteroid.to_feature_dict()["object_key"] == "history-only"
    assert "close_approach_count" not in asteroid.to_feature_dict()


def test_close_approach_summary_priority_indicator() -> None:
    summary = CloseApproachSummary(
        min_close_approach_dist=0.03,
        min_close_approach_dist_min=0.02,
        max_close_approach_v_rel=25.0,
        close_approach_count=5,
    )

    assert summary.has_close_approach_data()
    assert summary.approach_priority_indicator() is not None


def test_factory_builds_asteroid_from_gold_row_and_detailed_cad_row() -> None:
    gold_asteroid = AsteroidFactory.from_gold_row(
        {
            "object_key": "100",
            "name": "Gold NEO",
            "e": 0.1,
            "a": 1.2,
            "q": 0.9,
            "i": 1.0,
            "h": 21.0,
            "min_close_approach_dist": 0.04,
            "max_close_approach_v_rel": 19.0,
            "close_approach_count": 3,
        }
    )
    detailed_asteroid = AsteroidFactory.from_gold_row(
        {
            "object_key": "200",
            "name": "CAD NEO",
            "close_approaches": [
                {
                    "close_approach_datetime": "2030-Jan-01 00:00",
                    "dist": 0.02,
                    "dist_min": 0.01,
                    "v_rel": 22.0,
                    "body": "Earth",
                }
            ],
        }
    )

    assert gold_asteroid.close_approach_history is None
    assert gold_asteroid.close_approach_summary.close_approach_count == 3
    assert detailed_asteroid.close_approach_history is not None
    assert detailed_asteroid.close_approach_summary.min_close_approach_dist_min == 0.01
    assert detailed_asteroid.close_approach_summary.close_approach_count == 1
