from __future__ import annotations

from neo_ange.risk.categories import RiskCategoryAssigner


def test_categories_by_threshold() -> None:
    assigner = RiskCategoryAssigner()

    assert assigner.assign(0) == "low"
    assert assigner.assign(19.99) == "low"
    assert assigner.assign(20) == "moderate"
    assert assigner.assign(40) == "elevated"
    assert assigner.assign(60) == "high"
    assert assigner.assign(80) == "critical"


def test_describe_and_extremes() -> None:
    assigner = RiskCategoryAssigner()

    assert "not an official alert" in assigner.describe("low").lower()
    assert assigner.assign(-10) == "low"
    assert assigner.assign(999) == "critical"
    assert "unknown" in assigner.describe("missing").lower()
