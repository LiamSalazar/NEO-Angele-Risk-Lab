from __future__ import annotations

from neo_ange.domain.approach import CloseApproach, CloseApproachHistory, CloseApproachSummary


def test_close_approach_indicators_are_bounded() -> None:
    approach = CloseApproach(dist_min=0.01, v_rel=25.0)

    assert approach.distance_indicator() is not None
    assert approach.velocity_indicator() == 0.5


def test_close_approach_history_selects_closest_fastest_and_next() -> None:
    slow_close = CloseApproach(
        close_approach_datetime="2031-Jan-01 00:00",
        dist=0.03,
        dist_min=0.02,
        v_rel=12.0,
        body="Earth",
    )
    fast_far = CloseApproach(
        close_approach_datetime="2029-Jan-01 00:00",
        dist=0.10,
        dist_min=0.08,
        v_rel=31.0,
        body="Earth",
    )
    history = CloseApproachHistory((slow_close, fast_far))

    assert history.count() == 2
    assert history.has_approaches()
    assert history.closest() == slow_close
    assert history.fastest() == fast_far
    assert history.next_approach() == fast_far


def test_close_approach_history_summarizes_to_existing_summary_object() -> None:
    history = CloseApproachHistory(
        (
            CloseApproach(
                close_approach_datetime="2031-Jan-01 00:00",
                dist=0.03,
                dist_min=0.02,
                v_rel=12.0,
            ),
            CloseApproach(
                close_approach_datetime="2029-Jan-01 00:00",
                dist=0.10,
                dist_min=0.08,
                v_rel=31.0,
            ),
        )
    )

    summary = history.summarize()

    assert isinstance(summary, CloseApproachSummary)
    assert summary.min_close_approach_dist == 0.03
    assert summary.min_close_approach_dist_min == 0.02
    assert summary.max_close_approach_v_rel == 31.0
    assert summary.next_close_approach_datetime == "2029-Jan-01 00:00"
    assert summary.close_approach_count == 2
    assert summary.approach_priority_indicator() is not None
    assert history.to_dict()["close_approach_count"] == 2


def test_empty_close_approach_history_summarizes_safely() -> None:
    history = CloseApproachHistory()

    summary = history.summarize()

    assert history.count() == 0
    assert not history.has_approaches()
    assert history.closest() is None
    assert history.fastest() is None
    assert history.next_approach() is None
    assert isinstance(summary, CloseApproachSummary)
    assert not summary.has_close_approach_data()
