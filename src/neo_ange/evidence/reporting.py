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
        eval_predictions, full_predictions, tabular_metrics = run_tabular_predictions(
            source_df,
            target=target,
        )
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
        eval_prediction_df = pd.DataFrame(eval_predictions)
        full_prediction_df = pd.DataFrame(full_predictions)
        user_facing_predictions = _user_facing_predictions(full_prediction_df)
        disagreements = build_disagreements(user_facing_predictions)
        high_confidence = _filter_predictions(full_prediction_df, confidence="high")
        low_confidence = _filter_predictions(full_prediction_df, confidence="low")
        false_positives = _filter_errors(full_prediction_df, actual=0, predicted=1)
        false_negatives = _filter_errors(full_prediction_df, actual=1, predicted=0)
        summary = _summary_payload(
            metrics=metrics,
            cards=cards,
            eval_predictions=eval_prediction_df,
            full_predictions=full_prediction_df,
            disagreements=disagreements,
            target=target,
            gold_df=gold_df,
            risk_df=risk_df,
            source_df=source_df,
        )
        payload = {
            "status": "success" if metrics else "missing_data",
            "target": target,
            "summary": summary,
            "model_cards": cards,
            "metrics": metrics,
            "prediction_count": int(len(full_prediction_df)),
            "prediction_rows_eval": int(len(eval_prediction_df)),
            "prediction_rows_full": int(len(full_prediction_df)),
            "disagreement_count": int(len(disagreements)),
        }
        if write:
            payload["outputs"] = self.write_outputs(
                payload=payload,
                eval_predictions=eval_prediction_df,
                full_predictions=full_prediction_df,
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
            "prediction_rows_eval": summary.get("prediction_rows_eval", 0) if summary else 0,
            "unique_eval_object_keys": (
                summary.get("unique_eval_object_keys", 0) if summary else 0
            ),
            "prediction_rows_full": summary.get("prediction_rows_full", 0) if summary else 0,
            "unique_full_object_keys": (
                summary.get("unique_full_object_keys", 0) if summary else 0
            ),
            "coverage_ratio": summary.get("coverage_ratio", 0) if summary else 0,
            "full_inference_available": (
                summary.get("full_inference_available", False) if summary else False
            ),
            "disagreement_count": summary.get("disagreement_count", 0) if summary else 0,
        }

    def read_summary(self) -> dict[str, Any]:
        """Read the saved summary."""
        return _read_json(self.report_dir / "model_evidence_summary.json")

    def read_cards(self) -> dict[str, Any]:
        """Read saved model cards."""
        return _read_json(self.report_dir / "model_cards.json")

    def read_predictions(self, mode: str = "full") -> dict[str, Any]:
        """Read saved prediction rows."""
        path = self._prediction_path(mode)
        if not path.exists():
            return {"status": "missing_data", "predictions": []}
        df = pd.read_csv(path)
        return {
            "status": "success",
            "mode": _normalize_prediction_mode(mode),
            "row_count": int(len(df)),
            "unique_object_keys": _unique_object_count(df),
            "predictions": to_jsonable(df.to_dict("records")),
        }

    def read_disagreements(self) -> dict[str, Any]:
        """Read saved disagreement rows."""
        path = self.report_dir / "model_disagreements.csv"
        if not path.exists():
            return {"status": "missing_data", "disagreements": []}
        df = pd.read_csv(path)
        return {"status": "success", "disagreements": to_jsonable(df.to_dict("records"))}

    def object_evidence(self, object_key: str, mode: str = "full") -> dict[str, Any]:
        """Read prediction/disagreement rows for one object."""
        predictions = self.read_predictions(mode=mode).get("predictions", [])
        rows = [row for row in predictions if str(row.get("object_key")) == str(object_key)]
        disagreements = self.read_disagreements().get("disagreements", [])
        object_disagreements = [
            row for row in disagreements if str(row.get("object_key")) == str(object_key)
        ]
        return {
            "status": "success" if rows or object_disagreements else "not_found",
            "object_key": object_key,
            "mode": _normalize_prediction_mode(mode),
            "predictions": rows,
            "disagreements": object_disagreements,
        }

    def _prediction_path(self, mode: str) -> Path:
        normalized = _normalize_prediction_mode(mode)
        if normalized == "eval":
            return self.report_dir / "model_predictions_eval.csv"
        full_path = self.report_dir / "model_predictions_full.csv"
        if full_path.exists():
            return full_path
        return self.report_dir / "model_predictions.csv"

    def write_outputs(
        self,
        *,
        payload: dict[str, Any],
        eval_predictions: pd.DataFrame,
        full_predictions: pd.DataFrame,
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
        eval_predictions_path = self.report_dir / "model_predictions_eval.csv"
        eval_predictions_parquet = self.report_dir / "model_predictions_eval.parquet"
        full_predictions_path = self.report_dir / "model_predictions_full.csv"
        full_predictions_parquet = self.report_dir / "model_predictions_full.parquet"
        disagreements_path = self.report_dir / "model_disagreements.csv"
        high_confidence_path = self.report_dir / "high_confidence_predictions.csv"
        low_confidence_path = self.report_dir / "low_confidence_predictions.csv"
        false_positives_path = self.report_dir / "false_positives.csv"
        false_negatives_path = self.report_dir / "false_negatives.csv"
        _write_prediction_frame(eval_predictions, eval_predictions_path, eval_predictions_parquet)
        _write_prediction_frame(full_predictions, full_predictions_path, full_predictions_parquet)
        _write_prediction_frame(full_predictions, predictions_path, predictions_parquet)
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
                "prediction_rows_eval": payload["prediction_rows_eval"],
                "prediction_rows_full": payload["prediction_rows_full"],
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
                "prediction_rows_eval": payload["prediction_rows_eval"],
                "prediction_rows_full": payload["prediction_rows_full"],
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
            "model_predictions_eval_parquet": str(eval_predictions_parquet),
            "model_predictions_eval_csv": str(eval_predictions_path),
            "model_predictions_full_parquet": str(full_predictions_parquet),
            "model_predictions_full_csv": str(full_predictions_path),
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
    eval_predictions: pd.DataFrame,
    full_predictions: pd.DataFrame,
    disagreements: pd.DataFrame,
    target: str,
    gold_df: pd.DataFrame,
    risk_df: pd.DataFrame,
    source_df: pd.DataFrame,
) -> dict[str, Any]:
    best_overall = _with_card_context(_best_metric(metrics, defensible_only=False), cards)
    best_defensible = _with_card_context(_best_metric(metrics, defensible_only=True), cards)
    best_graph = _with_card_context(
        _best_metric(metrics, model_families={"graph", "gnn"}),
        cards,
    )
    best_no_definition = _with_card_context(
        _best_metric(metrics, feature_sets={"no_definition_features", "orbital_only"}),
        cards,
    )
    total_gold_objects = _unique_object_count(gold_df)
    total_risk_objects = _unique_object_count(risk_df)
    total_active_objects = (
        total_risk_objects or total_gold_objects or _unique_object_count(source_df)
    )
    unique_full_object_keys = _unique_object_count(full_predictions)
    coverage_ratio = (
        round(unique_full_object_keys / total_active_objects, 6) if total_active_objects else 0.0
    )
    main_conclusion = _main_conclusion(best_defensible, len(disagreements))
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
        "status": "success" if metrics else "missing_data",
        "target": target,
        "total_gold_objects": total_gold_objects,
        "total_risk_objects": total_risk_objects,
        "prediction_rows_eval": int(len(eval_predictions)),
        "unique_eval_object_keys": _unique_object_count(eval_predictions),
        "prediction_rows_full": int(len(full_predictions)),
        "unique_full_object_keys": unique_full_object_keys,
        "coverage_ratio": coverage_ratio,
        "models_used": _models_used(metrics),
        "best_overall_metric": best_overall,
        "best_defensible_model": best_defensible,
        "best_defensible_model_interpretation": _best_interpretation(best_defensible),
        "best_graph_based_evidence": best_graph,
        "best_no_definition_feature_model": best_no_definition,
        "leakage_sensitive_models": leakage_sensitive,
        "disagreement_count": int(len(disagreements)),
        "prediction_count": int(len(full_predictions)),
        "full_inference_available": bool(
            total_active_objects and unique_full_object_keys >= total_active_objects
        ),
        "eval_predictions_path": str(Path("reports/model_evidence/model_predictions_eval.parquet")),
        "full_predictions_path": str(Path("reports/model_evidence/model_predictions_full.parquet")),
        "ranking_source": "Risk Priority Score",
        "recommended_use": "secondary evidence",
        "main_evidence_conclusion": main_conclusion,
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
        "leakage_risk": leakage_risk_for_feature_set(str(row.get("feature_set"))),
        "selection_metric": score,
        "metrics": row.get("metrics", {}),
    }


def _with_card_context(
    metric: dict[str, Any] | None,
    cards: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not metric:
        return None
    enriched = dict(metric)
    for card in cards:
        if (
            card.get("model_name") == metric.get("model_name")
            and card.get("feature_set") == metric.get("feature_set")
            and card.get("model_family") == metric.get("model_family")
        ):
            enriched.update(
                {
                    "leakage_risk": card.get("leakage_risk"),
                    "recommended_use": card.get("recommended_use"),
                    "not_recommended_use": card.get("not_recommended_use"),
                    "interpretation": card.get("interpretation"),
                    "strengths": card.get("strengths", []),
                    "limitations": card.get("weaknesses", []),
                    "status": card.get("status"),
                }
            )
            break
    return enriched


def _best_interpretation(best_defensible: dict[str, Any] | None) -> str:
    if not best_defensible:
        return "No defensible model evidence is available yet."
    return str(
        best_defensible.get("interpretation")
        or (
            f"{best_defensible.get('model_name')} on {best_defensible.get('feature_set')} "
            "provides secondary evidence for pattern consistency."
        )
    )


def _models_used(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in metrics:
        if row.get("status") not in {"success", "partial_success"}:
            continue
        model_name = str(row.get("model_name"))
        feature_set = str(row.get("feature_set"))
        model_family = str(row.get("model_family"))
        key = (model_name, feature_set, model_family)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "model_name": model_name,
                "model_family": model_family,
                "feature_set": feature_set,
                "target": row.get("target"),
                "leakage_risk": leakage_risk_for_feature_set(feature_set),
                "status": row.get("status"),
            }
        )
    return rows


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


def _user_facing_predictions(predictions: pd.DataFrame) -> pd.DataFrame:
    if predictions.empty or "leakage_risk" not in predictions.columns:
        return predictions
    return predictions[predictions["leakage_risk"] != "high"].copy()


def _unique_object_count(df: pd.DataFrame) -> int:
    if df.empty or "object_key" not in df.columns:
        return 0
    return int(df["object_key"].dropna().astype(str).nunique())


def _normalize_prediction_mode(mode: str) -> str:
    return "eval" if str(mode).lower() == "eval" else "full"


def _write_prediction_frame(df: pd.DataFrame, csv_path: Path, parquet_path: Path) -> None:
    df.to_csv(csv_path, index=False)
    if not df.empty:
        df.to_parquet(parquet_path, index=False)
    else:
        pd.DataFrame().to_parquet(parquet_path, index=False)


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
