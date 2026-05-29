"""Shared constants for graph-learning experiments."""

from __future__ import annotations

GNN_EXPERIMENT_VERSION = "gnn_research_lab_v1"
GRAPH_VERSION = "orbital_similarity_graph_v1"

SIMILARITY_FEATURES = [
    "e",
    "a",
    "q",
    "i",
    "om",
    "w",
    "ma",
    "n",
    "per",
    "ad",
    "moid",
    "h",
    "diameter",
    "risk_score_0_100",
]

FORBIDDEN_GRAPH_FEATURES = {
    "pha",
    "neo",
    "object_key",
    "spkid",
    "des",
    "full_name",
    "name",
    "risk_category",
    "built_at_utc",
    "source_availability_json",
    "next_close_approach_datetime",
}

GRAPH_NODE_FEATURES = [
    "e",
    "a",
    "q",
    "i",
    "om",
    "w",
    "ma",
    "n",
    "per",
    "ad",
    "moid",
    "moid_ld",
    "h",
    "diameter",
    "albedo",
    "min_close_approach_dist",
    "max_close_approach_v_rel",
    "close_approach_count",
    "sentry_flag",
    "sentry_ip",
    "feature_completeness_ratio",
    "risk_score_0_100",
]

GNN_STATUSES = {
    "success",
    "partial_success",
    "insufficient_data",
    "skipped_missing_dependency",
    "failed",
}
