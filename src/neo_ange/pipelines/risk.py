"""Pipeline orchestration for experimental risk-priority scoring."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from neo_ange.manifests.run_manifest import (
    RunManifest,
    create_run_id,
    list_manifests,
    load_latest_manifest,
    save_manifest,
    utc_now_manifest,
)
from neo_ange.risk.categories import RiskCategoryAssigner
from neo_ange.risk.explanations import RiskExplanationService
from neo_ange.risk.ranking import RiskRankingService
from neo_ange.risk.reporting import RiskReportWriter
from neo_ange.risk.schemas import RISK_SCORE_VERSION
from neo_ange.risk.scoring import RiskScorer
from neo_ange.utils.paths import contains_files
from neo_ange.utils.serialization import to_jsonable


class RiskPipeline:
    """Load gold features, compute scores, and persist risk reports."""

    def __init__(
        self,
        gold_root: str | Path = "data/gold",
        risk_output_dir: str | Path | None = None,
        report_dir: str | Path = "reports/risk",
        manifest_dir: str | Path = "reports/manifests",
        scorer: RiskScorer | None = None,
    ) -> None:
        self.gold_root = Path(gold_root)
        self.features_path = self.gold_root / "neo_risk_features"
        self.risk_output_dir = Path(risk_output_dir) if risk_output_dir else self.gold_root / "risk_scores"
        self.report_dir = Path(report_dir)
        self.manifest_dir = Path(manifest_dir)
        self.scorer = scorer or RiskScorer()
        self.ranking = RiskRankingService()
        self.explanations = RiskExplanationService()
        self.report_writer = RiskReportWriter(self.risk_output_dir, self.report_dir)

    @property
    def risk_scores_path(self) -> Path:
        """Return the expected scored parquet file path."""
        return self.risk_output_dir / "risk_scores.parquet"

    def load_gold_features(self) -> pd.DataFrame:
        """Load the gold ``neo_risk_features`` table, or an empty frame if absent."""
        if not contains_files(self.features_path, "*.parquet"):
            return pd.DataFrame()
        return pd.read_parquet(self.features_path)

    def load_risk_scores(self) -> pd.DataFrame:
        """Load saved risk scores, or an empty frame if absent."""
        if self.risk_scores_path.exists():
            return pd.read_parquet(self.risk_scores_path)
        if contains_files(self.risk_output_dir, "*.parquet"):
            return pd.read_parquet(self.risk_output_dir)
        return pd.DataFrame()

    def build_scores(self) -> dict[str, Any]:
        """Compute scores from gold features, persist outputs, and save a manifest."""
        run_id = create_run_id("risk")
        started_at = utc_now_manifest()
        warnings: list[str] = []
        errors: list[str] = []
        outputs: dict[str, Any] = {}
        metrics: dict[str, Any] = {}

        df = self.load_gold_features()
        if df.empty:
            errors.append("Gold features not found. Run: python -m neo_ange.cli etl run-all")
            result = self._result("failed", outputs, metrics, warnings, errors)
            result["manifest_path"] = str(self._save_manifest(run_id, started_at, result))
            return result

        if len(df) < 100:
            warnings.append(
                f"Risk ranking is exploratory: only {len(df)} object(s) are available."
            )

        scored_df = self.scorer.score_dataframe(df)
        summary = self.ranking.summarize_ranking(scored_df)
        summary["score_version"] = self.scorer.score_version()
        summary["warnings"] = warnings
        outputs = self.report_writer.save_outputs(
            scored_df=scored_df,
            summary=summary,
            weights=self.scorer.weights,
        )
        metrics = {
            "gold_row_count": int(len(df)),
            "scored_row_count": int(len(scored_df)),
            "score_version": self.scorer.score_version(),
            **summary,
        }
        status = "partial_success" if warnings else "success"
        result = self._result(status, outputs, metrics, warnings, errors)
        manifest_path = self._save_manifest(run_id, started_at, result)
        result["outputs"]["manifest_path"] = str(manifest_path)
        result["manifest_path"] = str(manifest_path)
        return to_jsonable(result)

    def top(self, limit: int = 20) -> list[dict[str, Any]]:
        """Return top ranked scored objects."""
        df = self.load_risk_scores()
        if df.empty:
            return []
        return to_jsonable(self.ranking.rank(df, limit=limit).to_dict(orient="records"))

    def explain(self, object_key: str) -> dict[str, Any]:
        """Return an explanation for a scored object."""
        df = self.load_risk_scores()
        if df.empty:
            return {
                "status": "missing_data",
                "object_key": object_key,
                "message": "Risk scores not found. Run: python -m neo_ange.cli risk build",
            }
        row = self.ranking.get_object(df, object_key)
        if row is None:
            return {
                "status": "not_found",
                "object_key": object_key,
                "message": f"Object '{object_key}' was not found in risk scores.",
            }
        explanation = self.explanations.explain_row(row)
        explanation["status"] = "success"
        return to_jsonable(explanation)

    def status(self) -> dict[str, Any]:
        """Return data/report availability for the risk pipeline."""
        risk_df = self.load_risk_scores()
        latest_reports = _latest_paths(self.report_dir, ["*.json", "*.csv", "*.md"])
        latest_manifests = [str(path) for path in list_manifests("risk", self.manifest_dir)[-5:]]
        latest_manifest = load_latest_manifest("risk", self.manifest_dir)
        return {
            "status": "ok",
            "gold_features_available": contains_files(self.features_path, "*.parquet"),
            "risk_scores_available": not risk_df.empty,
            "risk_scores_path": str(self.risk_scores_path),
            "row_count": int(len(risk_df)),
            "latest_reports": [str(path) for path in latest_reports],
            "latest_manifests": latest_manifests,
            "latest_manifest_status": latest_manifest.get("status") if latest_manifest else None,
            "score_version": RISK_SCORE_VERSION,
        }

    def categories(self) -> dict[str, Any]:
        """Return configured category metadata."""
        return RiskCategoryAssigner().all_categories()

    def methodology(self) -> dict[str, Any]:
        """Return the methodology report path and content when available."""
        path = self.report_dir / "risk_methodology.md"
        if not path.exists():
            path = self.report_writer.write_methodology(self.scorer.weights)
        return {"path": str(path), "content": path.read_text(encoding="utf-8")}

    def _save_manifest(
        self,
        run_id: str,
        started_at: str,
        result: dict[str, Any],
    ) -> Path:
        manifest = RunManifest(
            run_id=run_id,
            run_type="risk",
            started_at_utc=started_at,
            ended_at_utc=utc_now_manifest(),
            status=result["status"],
            inputs={"gold_features_path": str(self.features_path)},
            outputs=result.get("outputs", {}),
            metrics=result.get("metrics_summary", {}),
            warnings=result.get("warnings", []),
            errors=result.get("errors", []),
        )
        return save_manifest(manifest, output_dir=self.manifest_dir)

    def _result(
        self,
        status: str,
        outputs: dict[str, Any],
        metrics: dict[str, Any],
        warnings: list[str],
        errors: list[str],
    ) -> dict[str, Any]:
        return {
            "status": status,
            "outputs": outputs,
            "metrics_summary": metrics,
            "warnings": warnings,
            "errors": errors,
        }


def _latest_paths(root: Path, patterns: list[str], limit: int = 5) -> list[Path]:
    if not root.exists():
        return []
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(path for path in root.glob(pattern) if path.is_file())
    return sorted(paths, key=lambda path: path.stat().st_mtime, reverse=True)[:limit]


def read_risk_summary(report_dir: str | Path = "reports/risk") -> dict[str, Any] | None:
    """Read the latest risk summary JSON when present."""
    path = Path(report_dir) / "risk_scores_summary.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
