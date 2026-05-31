"""Model-card helpers for tabular and graph evidence."""

from __future__ import annotations

from typing import Any

from neo_ange.evidence.schemas import ModelCard

LEAKAGE_HIGH_FEATURE_SETS = {
    "full_features",
    "definition_features_only",
    "risk_score_features",
    "graph_node_features",
}
LEAKAGE_MEDIUM_FEATURE_SETS = {"sentry_related"}


def leakage_risk_for_feature_set(feature_set: str) -> str:
    """Classify leakage risk from the feature-set name."""
    if feature_set in LEAKAGE_HIGH_FEATURE_SETS:
        return "high"
    if feature_set in LEAKAGE_MEDIUM_FEATURE_SETS:
        return "medium"
    return "low"


def build_model_card(
    *,
    model_name: str,
    model_family: str,
    feature_set: str,
    target: str,
    metrics: dict[str, Any],
    status: str = "success",
) -> dict[str, Any]:
    """Build an interpretive card for one evidence result."""
    leakage_risk = leakage_risk_for_feature_set(feature_set)
    if model_family in {"graph", "gnn"}:
        recommended = "Evidence of consistency between orbital neighborhoods and observed labels."
        weakness = "Graph baselines are sensitive to graph construction choices."
        interpretation = (
            "The graph model checks whether neighboring orbital contexts support the observed "
            "label pattern; it should not be read as impact prediction."
        )
        if model_family == "gnn" and status == "skipped_missing_dependency":
            recommended = "Dependency-readiness signal for advanced graph mode."
            weakness = "No GraphSAGE/GCN metrics are available until torch-geometric is installed."
            interpretation = (
                "Advanced GNN training was skipped and should not be compared as a metric."
            )
    elif leakage_risk == "low":
        recommended = "Defensible support for pattern consistency without PHA definition variables."
        weakness = "May understate patterns that depend on physical-size or MOID definition fields."
        interpretation = (
            "This model is useful as secondary evidence because it avoids direct definition-heavy "
            "features and focuses on orbital or contextual signals."
        )
    else:
        recommended = "Internal diagnostic for leakage-sensitive behavior."
        weakness = "Definition-adjacent inputs can make PHA metrics look stronger than they are."
        interpretation = (
            "High scores here validate that definition-related variables encode the label, but "
            "this is not the best user-facing evidence."
        )
    card = ModelCard(
        model_name=model_name,
        model_family=model_family,
        feature_set=feature_set,
        target=target,
        metrics=metrics,
        strengths=_strengths(metrics, leakage_risk),
        weaknesses=[weakness],
        leakage_risk=leakage_risk,
        recommended_use=recommended,
        not_recommended_use="Do not treat this as an official impact-risk or alerting model.",
        interpretation=interpretation,
        status=status,
    )
    return card.to_dict()


def _strengths(metrics: dict[str, Any], leakage_risk: str) -> list[str]:
    strengths = []
    if metrics.get("roc_auc") is not None:
        strengths.append("Produces probabilistic ranking evidence.")
    if metrics.get("recall") is not None:
        strengths.append("Provides a measurable check on positive-label retrieval.")
    if leakage_risk == "low":
        strengths.append("Avoids direct PHA definition variables.")
    return strengths or ["Provides a baseline comparison point."]
