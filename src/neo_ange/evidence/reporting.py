"""Build and persist model evidence artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from neo_ange.evidence.disagreement import build_disagreements
from neo_ange.evidence.model_cards import build_model_card, leakage_risk_for_feature_set
from neo_ange.evidence.predictions import add_graph_metric_records, run_tabular_predictions
from neo_ange.utils.serialization import to_jsonable, write_json


class ModelEvidenceBuilder:
    """Create model cards, predictions and disagreement artifacts."""

    def __init__(
        self,
        gold_root: str | Path = "data/gold",
        reports_root: str | Path = "reports",
    ) -> None:
        self.gold_root = Path(gold_root)
        self.reports_root = Path(reports_root)
        self.report_dir = self.reports_root / "model_evidence"

    def build(self, target: str = "pha", write: bool = True) -> dict[str, Any]:
        """Build model evidence from current gold/risk/graph artifacts."""
        risk_df = _read_parquet(self.gold_root / "risk_scores" / "risk_scores.parquet")
        gold_df = _read_parquet(self.gold_root / "neo_risk_features")
        source_df = _merge_score_columns(gold_df, risk_df)
        predictions, tabular_metrics = run_tabular_predictions(source_df, target=target)
        graph_metrics = add_graph_metric_records(
            _read_csv(self.reports_root / "gnn" / "gnn_metrics.csv"),
            target=target,
        )
        metrics = [*tabular_metrics, *graph_metrics]
        cards = [
            build_model_card(
                model_name=row["model_name"],
                model_family=row["model_family"],
                feature_set=row["feature_set"],
                target=row.get("target", target),
                metrics=row.get("metrics", {}),
                status=row.get("status", "success"),
            )
            for row in metrics
        ]
        prediction_df = pd.DataFrame(predictions)
        disagreements = build_disagreements(prediction_df)
        high_confidence = _filter_predictions(prediction_df, confidence="high")
        low_confidence = _filter_predictions(prediction_df, confidence="low")
        false_positives = _filter_errors(prediction_df, actual=0, predicted=1)
        false_negatives = _filter_errors(prediction_df, actual=1, predicted=0)
        summary = _summary_payload(
            metrics=metrics,
            cards=cards,
            predictions=prediction_df,
            disagreements=disagreements,
            target=target,
        )
        payload = {
            "status": "success" if metrics else "missing_data",
            "target": target,
            "summary": summary,
            "model_cards": cards,
            "metrics": metrics,
            "prediction_count": int(len(prediction_df)),
            "disagreement_count": int(len(disagreements)),
        }
        if write:
            payload["outputs"] = self.write_outputs(
                payload=payload,
                predictions=prediction_df,
                disagreements=disagreements,
                high_confidence=high_confidence,
                low_confidence=low_confidence,
                false_positives=false_positives,
                false_negatives=false_negatives,
            )
        return to_jsonable(payload)

    def status(self) -> dict[str, Any]:
        """Return model-evidence availability."""
        summary = self.read_summary()
        return {
            "status": summary.get("status", "missing_data") if summary else "missing_data",
            "report_dir": str(self.report_dir),
            "prediction_count": summary.get("prediction_count", 0) if summary else 0,
            "disagreement_count": summary.get("disagreement_count", 0) if summary else 0,
        }

    def read_summary(self) -> dict[str, Any]:
        """Read the saved summary."""
        return _read_json(self.report_dir / "model_evidence_summary.json")

    def read_cards(self) -> dict[str, Any]:
        """Read saved model cards."""
        return _read_json(self.report_dir / "model_cards.json")

    def read_predictions(self) -> dict[str, Any]:
        """Read saved prediction rows."""
        path = self.report_dir / "model_predictions.csv"
        if not path.exists():
            return {"status": "missing_data", "predictions": []}
        df = pd.read_csv(path)
        return {"status": "success", "predictions": to_jsonable(df.to_dict("records"))}

    def read_disagreements(self) -> dict[str, Any]:
        """Read saved disagreement rows."""
        path = self.report_dir / "model_disagreements.csv"
        if not path.exists():
            return {"status": "missing_data", "disagreements": []}
        df = pd.read_csv(path)
        return {"status": "success", "disagreements": to_jsonable(df.to_dict("records"))}

    def object_evidence(self, object_key: str) -> dict[str, Any]:
        """Read prediction/disagreement rows for one object."""
        predictions = self.read_predictions().get("predictions", [])
        rows = [row for row in predictions if str(row.get("object_key")) == str(object_key)]
        disagreements = self.read_disagreements().get("disagreements", [])
        object_disagreements = [
            row for row in disagreements if str(row.get("object_key")) == str(object_key)
        ]
        return {
            "status": "success" if rows or object_disagreements else "not_found",
            "object_key": object_key,
            "predictions": rows,
            "disagreements": object_disagreements,
        }

    def write_outputs(
        self,
        *,
        payload: dict[str, Any],
        predictions: pd.DataFrame,
        disagreements: pd.DataFrame,
        high_confidence: pd.DataFrame,
        low_confidence: pd.DataFrame,
        false_positives: pd.DataFrame,
        false_negatives: pd.DataFrame,
    ) -> dict[str, str]:
        """Persist model evidence outputs."""
        self.report_dir.mkdir(parents=True, exist_ok=True)
        predictions_path = self.report_dir / "model_predictions.csv"
        predictions_parquet = self.report_dir / "model_predictions.parquet"
        disagreements_path = self.report_dir / "model_disagreements.csv"
        high_confidence_path = self.report_dir / "high_confidence_predictions.csv"
        low_confidence_path = self.report_dir / "low_confidence_predictions.csv"
        false_positives_path = self.report_dir / "false_positives.csv"
        false_negatives_path = self.report_dir / "false_negatives.csv"
        predictions.to_csv(predictions_path, index=False)
        if not predictions.empty:
            predictions.to_parquet(predictions_parquet, index=False)
        else:
            pd.DataFrame().to_parquet(predictions_parquet, index=False)
        disagreements.to_csv(disagreements_path, index=False)
        high_confidence.to_csv(high_confidence_path, index=False)
        low_confidence.to_csv(low_confidence_path, index=False)
        false_positives.to_csv(false_positives_path, index=False)
        false_negatives.to_csv(false_negatives_path, index=False)
        summary_path = write_json(
            {
                "status": payload["status"],
                **payload["summary"],
                "prediction_count": payload["prediction_count"],
                "disagreement_count": payload["disagreement_count"],
            },
            self.report_dir / "model_evidence_summary.json",
        )
        cards_path = write_json(
            {"status": payload["status"], "model_cards": payload["model_cards"]},
            self.report_dir / "model_cards.json",
        )
        runtime_path = write_json(
            {
                "status": payload["status"],
                "note": (
                    "Runtime is measured by the benchmark module; this file records "
                    "artifact counts."
                ),
                "prediction_count": payload["prediction_count"],
                "metric_count": len(payload["metrics"]),
            },
            self.report_dir / "benchmark_runtime.json",
        )
        markdown_path = _write_markdown(
            self.report_dir / "model_evidence_summary.md",
            payload["summary"],
            payload["model_cards"],
        )
        return {
            "model_evidence_summary_json": str(summary_path),
            "model_evidence_summary_markdown": str(markdown_path),
            "model_cards": str(cards_path),
            "model_predictions_parquet": str(predictions_parquet),
            "model_predictions_csv": str(predictions_path),
            "model_disagreements_csv": str(disagreements_path),
            "high_confidence_predictions_csv": str(high_confidence_path),
            "low_confidence_predictions_csv": str(low_confidence_path),
            "false_positives_csv": str(false_positives_path),
            "false_negatives_csv": str(false_negatives_path),
            "benchmark_runtime_json": str(runtime_path),
        }


def _read_parquet(path: Path) -> pd.DataFrame:
    if path.is_file():
        return pd.read_parquet(path)
    if path.is_dir() and any(path.glob("*.parquet")):
        return pd.read_parquet(path)
    return pd.DataFrame()


def _read_csv(path: Path) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _merge_score_columns(gold_df: pd.DataFrame, risk_df: pd.DataFrame) -> pd.DataFrame:
    if gold_df.empty:
        return risk_df.copy()
    if risk_df.empty or "object_key" not in risk_df.columns:
        return gold_df.copy()
    score_columns = [
        column
        for column in [
            "object_key",
            "risk_score_0_100",
            "risk_category",
            "risk_explanation_short",
        ]
        if column in risk_df.columns
    ]
    merged = gold_df.merge(risk_df[score_columns], on="object_key", how="left")
    return merged


def _summary_payload(
    *,
    metrics: list[dict[str, Any]],
    cards: list[dict[str, Any]],
    predictions: pd.DataFrame,
    disagreements: pd.DataFrame,
    target: str,
) -> dict[str, Any]:
    best_overall = _best_metric(metrics, defensible_only=False)
    best_defensible = _best_metric(metrics, defensible_only=True)
    best_graph = _best_metric(metrics, model_families={"graph", "gnn"})
    best_no_definition = _best_metric(
        metrics, feature_sets={"no_definition_features", "orbital_only"}
    )
    leakage_sensitive = [
        {
            "model_name": card["model_name"],
            "feature_set": card["feature_set"],
            "leakage_risk": card["leakage_risk"],
        }
        for card in cards
        if card.get("leakage_risk") == "high"
    ]
    return {
        "target": target,
        "best_overall_metric": best_overall,
        "best_defensible_model": best_defensible,
        "best_graph_based_evidence": best_graph,
        "best_no_definition_feature_model": best_no_definition,
        "leakage_sensitive_models": leakage_sensitive,
        "disagreement_count": int(len(disagreements)),
        "prediction_count": int(len(predictions)),
        "main_evidence_conclusion": _main_conclusion(best_defensible, len(disagreements)),
    }


def _best_metric(
    metrics: list[dict[str, Any]],
    *,
    defensible_only: bool = False,
    model_families: set[str] | None = None,
    feature_sets: set[str] | None = None,
) -> dict[str, Any] | None:
    candidates = []
    for row in metrics:
        if row.get("status") not in {"success", "partial_success"}:
            continue
        feature_set = str(row.get("feature_set"))
        if defensible_only and leakage_risk_for_feature_set(feature_set) != "low":
            continue
        if model_families and row.get("model_family") not in model_families:
            continue
        if feature_sets and feature_set not in feature_sets:
            continue
        metric_values = row.get("metrics", {})
        score = metric_values.get("pr_auc")
        if score is None:
            score = metric_values.get("f1")
        if score is None:
            continue
        candidates.append((float(score), row))
    if not candidates:
        return None
    score, row = max(candidates, key=lambda item: item[0])
    return {
        "model_name": row.get("model_name"),
        "model_family": row.get("model_family"),
        "feature_set": row.get("feature_set"),
        "target": row.get("target"),
        "selection_metric": score,
        "metrics": row.get("metrics", {}),
    }


def _main_conclusion(best_defensible: dict[str, Any] | None, disagreement_count: int) -> str:
    if not best_defensible:
        return "No defensible model evidence is available yet."
    return (
        f"{best_defensible['model_name']} on {best_defensible['feature_set']} provides "
        "secondary evidence for pattern consistency; disagreements remain an inspection queue "
        f"({disagreement_count} rows)."
    )


def _filter_predictions(predictions: pd.DataFrame, confidence: str) -> pd.DataFrame:
    if predictions.empty:
        return pd.DataFrame()
    return predictions[predictions["confidence_bucket"] == confidence].copy()


def _filter_errors(predictions: pd.DataFrame, actual: int, predicted: int) -> pd.DataFrame:
    if predictions.empty:
        return pd.DataFrame()
    return predictions[
        (predictions["actual_label"].astype(int) == actual)
        & (predictions["predicted_label"].astype(int) == predicted)
    ].copy()


def _write_markdown(path: Path, summary: dict[str, Any], cards: list[dict[str, Any]]) -> Path:
    lines = [
        "# Model Evidence Summary",
        "",
        summary.get("main_evidence_conclusion", "No model evidence conclusion available."),
        "",
        "## Best Evidence",
        "",
        f"- Best overall metric: {summary.get('best_overall_metric')}",
        f"- Best defensible model: {summary.get('best_defensible_model')}",
        f"- Best graph-based evidence: {summary.get('best_graph_based_evidence')}",
        f"- Disagreement rows: {summary.get('disagreement_count')}",
        "",
        "## Model Cards",
        "",
    ]
    for card in cards:
        lines.extend(
            [
                f"### {card['model_name']} / {card['feature_set']}",
                "",
                f"- Family: {card['model_family']}",
                f"- Target: {card['target']}",
                f"- Leakage risk: {card['leakage_risk']}",
                f"- Recommended use: {card['recommended_use']}",
                f"- Interpretation: {card['interpretation']}",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
