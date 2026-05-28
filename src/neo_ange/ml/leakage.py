"""Leakage inspection for PHA baseline experiments."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from neo_ange.ml.feature_sets import DEFINITION_RELATED_COLUMNS, IDENTIFIER_OR_METADATA_COLUMNS
from neo_ange.utils.serialization import write_json

DIRECT_TARGET_LEAKAGE = {"pha"}
STRONG_PROXY_COLUMNS = {
    "inverse_moid",
    "log_diameter",
    "size_proxy_score",
    "proximity_proxy_score",
}


class LeakageAuditor:
    """Classify leakage risk and compare feature-set experiment outcomes."""

    def inspect_feature_leakage(
        self,
        feature_names: list[str],
        target: str = "pha",
    ) -> dict[str, Any]:
        """Categorize each feature by its relationship to the target definition."""
        direct = {target, *DIRECT_TARGET_LEAKAGE}
        categories: dict[str, list[str]] = {
            "direct_target_leakage": [],
            "definition_related": [],
            "strong_proxy": [],
            "safe_or_contextual": [],
            "identifier_or_metadata": [],
        }
        by_feature: dict[str, str] = {}
        for feature in feature_names:
            if feature in direct:
                category = "direct_target_leakage"
            elif feature in IDENTIFIER_OR_METADATA_COLUMNS:
                category = "identifier_or_metadata"
            elif feature in STRONG_PROXY_COLUMNS:
                category = "strong_proxy"
            elif feature in DEFINITION_RELATED_COLUMNS:
                category = "definition_related"
            else:
                category = "safe_or_contextual"
            categories[category].append(feature)
            by_feature[feature] = category
        return {"by_feature": by_feature, "categories": categories}

    def compare_feature_sets(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """Compare metrics across feature sets to flag possible trivial learning."""
        completed = [
            result
            for result in results
            if result.get("status") == "success" and isinstance(result.get("metrics"), dict)
        ]
        if not completed:
            return {
                "status": "insufficient_results",
                "signals": [],
                "conclusion": "No successful model results were available for leakage comparison.",
            }

        by_feature_set = _best_metric_by_feature_set(completed, metric_name="pr_auc")
        if not any(value is not None for value in by_feature_set.values()):
            by_feature_set = _best_metric_by_feature_set(completed, metric_name="f1")

        signals: list[str] = []
        full_score = by_feature_set.get("full_features")
        no_definition_score = by_feature_set.get("no_definition_features")
        definition_score = by_feature_set.get("definition_features_only")

        if (
            full_score is not None
            and no_definition_score is not None
            and full_score - no_definition_score >= 0.20
        ):
            signals.append(
                "full_features substantially outperformed no_definition_features, which may "
                "indicate reliance on PHA-definition variables or close proxies."
            )
        if definition_score is not None and definition_score >= 0.85:
            signals.append(
                "definition_features_only achieved very high performance, consistent with the "
                "label being largely recoverable from H/MOID-related variables."
            )
        if (
            definition_score is not None
            and no_definition_score is not None
            and definition_score - no_definition_score >= 0.20
        ):
            signals.append(
                "Performance dropped sharply after removing definition-related variables."
            )

        if signals:
            conclusion = (
                "The experiment pattern suggests likely definition leakage. Treat high scores "
                "from H, MOID, diameter, and derived proxies as a reproducibility check, not as "
                "evidence of independent hazard intelligence."
            )
            status = "warning"
        else:
            conclusion = (
                "No strong leakage pattern was detected from the available comparisons. This "
                "does not prove absence of leakage, especially with small or imbalanced data."
            )
            status = "ok"

        return {
            "status": status,
            "best_scores_by_feature_set": by_feature_set,
            "signals": signals,
            "conclusion": conclusion,
        }

    def generate_leakage_report(
        self,
        results: list[dict[str, Any]],
        output_dir: str | Path = "reports/ml",
    ) -> Path:
        """Generate JSON and Markdown leakage reports."""
        report_dir = Path(output_dir)
        report_dir.mkdir(parents=True, exist_ok=True)
        comparison = self.compare_feature_sets(results)
        features = sorted(
            {
                feature
                for result in results
                for feature in result.get("features", [])
                if isinstance(feature, str)
            }
        )
        inspection = self.inspect_feature_leakage(features)
        payload = {
            "status": comparison["status"],
            "comparison": comparison,
            "feature_inspection": inspection,
            "experiment_count": len(results),
        }
        json_path = write_json(payload, report_dir / "leakage_audit.json")
        markdown_path = report_dir / "leakage_audit.md"
        markdown_path.write_text(
            _leakage_markdown(payload=payload, json_path=json_path),
            encoding="utf-8",
        )
        return markdown_path


def _best_metric_by_feature_set(
    results: list[dict[str, Any]],
    metric_name: str,
) -> dict[str, float | None]:
    best: dict[str, float | None] = {}
    for result in results:
        feature_set = str(result.get("feature_set_name"))
        value = result.get("metrics", {}).get(metric_name)
        if value is None:
            best.setdefault(feature_set, None)
            continue
        numeric_value = float(value)
        current = best.get(feature_set)
        best[feature_set] = numeric_value if current is None else max(current, numeric_value)
    return best


def _leakage_markdown(payload: dict[str, Any], json_path: Path) -> str:
    comparison = payload["comparison"]
    categories = payload["feature_inspection"]["categories"]
    signals = comparison.get("signals") or ["No strong leakage signal was detected."]
    return "\n".join(
        [
            "# PHA Leakage Audit",
            "",
            "## What was compared",
            "",
            "Baseline experiments were compared across full, definition-only, "
            "definition-excluded, orbital, approach-quality, and Sentry-related feature sets.",
            "",
            "## Why H and MOID are sensitive",
            "",
            "PHA labels are commonly tied to absolute magnitude H and Earth MOID thresholds. "
            "Using H, MOID, diameter, or direct transformations of those fields can make a "
            "model reproduce the label definition instead of learning independent risk signals.",
            "",
            "## Signals observed",
            "",
            *[f"- {signal}" for signal in signals],
            "",
            "## Feature categories",
            "",
            f"- Direct target leakage: {', '.join(categories['direct_target_leakage']) or 'None'}",
            f"- Definition related: {', '.join(categories['definition_related']) or 'None'}",
            f"- Strong proxies: {', '.join(categories['strong_proxy']) or 'None'}",
            "- Identifier or metadata: "
            f"{', '.join(categories['identifier_or_metadata']) or 'None'}",
            "",
            "## Technical conclusion",
            "",
            comparison["conclusion"],
            "",
            "## Limitations",
            "",
            "The audit is only as reliable as the current gold dataset. Small sample sizes, "
            "few positives, duplicated objects, and source-selection effects can dominate "
            "reported metrics.",
            "",
            f"Machine-readable report: `{json_path}`",
            "",
        ]
    )
