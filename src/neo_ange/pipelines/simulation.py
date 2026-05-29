"""Pipeline orchestration for approximate Monte Carlo simulations."""

from __future__ import annotations

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
from neo_ange.simulation.monte_carlo import MonteCarloEngine
from neo_ange.simulation.reporting import SimulationReportWriter
from neo_ange.simulation.schemas import MONTE_CARLO_VERSION
from neo_ange.utils.paths import contains_files
from neo_ange.utils.serialization import to_jsonable


class SimulationPipeline:
    """Load risk scores, run Monte Carlo simulations, and save reports."""

    def __init__(
        self,
        gold_root: str | Path = "data/gold",
        risk_scores_dir: str | Path | None = None,
        simulation_output_dir: str | Path | None = None,
        report_dir: str | Path = "reports/simulation",
        manifest_dir: str | Path = "reports/manifests",
        engine: MonteCarloEngine | None = None,
    ) -> None:
        self.gold_root = Path(gold_root)
        self.risk_scores_dir = (
            Path(risk_scores_dir) if risk_scores_dir else self.gold_root / "risk_scores"
        )
        self.simulation_output_dir = (
            Path(simulation_output_dir)
            if simulation_output_dir
            else self.gold_root / "simulation_results"
        )
        self.report_dir = Path(report_dir)
        self.manifest_dir = Path(manifest_dir)
        self.engine = engine or MonteCarloEngine()
        self.report_writer = SimulationReportWriter(self.simulation_output_dir, self.report_dir)

    @property
    def risk_scores_path(self) -> Path:
        return self.risk_scores_dir / "risk_scores.parquet"

    @property
    def simulation_results_path(self) -> Path:
        return self.simulation_output_dir / "monte_carlo_results.parquet"

    def load_risk_scores(self) -> pd.DataFrame:
        """Load risk-score rows, or return an empty frame if absent."""
        if self.risk_scores_path.exists():
            return pd.read_parquet(self.risk_scores_path)
        if contains_files(self.risk_scores_dir, "*.parquet"):
            return pd.read_parquet(self.risk_scores_dir)
        return pd.DataFrame()

    def simulate_object(
        self,
        object_key: str,
        n_simulations: int = 1000,
        random_state: int | None = 42,
    ) -> dict[str, Any]:
        """Run Monte Carlo for one object and save reports/manifests."""
        run_id = create_run_id("simulation")
        started_at = utc_now_manifest()
        df = self.load_risk_scores()
        warnings: list[str] = []
        errors: list[str] = []
        if df.empty:
            errors.append("Risk scores not found. Run: python -m neo_ange.cli risk build")
            result = self._result("failed", {}, {}, warnings, errors)
            result["manifest_path"] = str(
                self._save_manifest(run_id, started_at, result, {"object_key": object_key})
            )
            return result

        row = _find_object(df, object_key)
        if row is None:
            errors.append(f"Object '{object_key}' was not found in risk scores.")
            result = self._result("not_found", {}, {}, warnings, errors)
            result["manifest_path"] = str(
                self._save_manifest(run_id, started_at, result, {"object_key": object_key})
            )
            return result

        summary = self.engine.simulate_object(
            row,
            n_simulations=n_simulations,
            random_state=random_state,
        )
        outputs = self.report_writer.save_outputs([summary])
        metrics = {"object_key": object_key, **summary}
        result = self._result("success", outputs, metrics, warnings, errors)
        manifest_path = self._save_manifest(
            run_id,
            started_at,
            result,
            {
                "object_key": object_key,
                "n_simulations": n_simulations,
                "random_state": random_state,
            },
        )
        result["outputs"]["manifest_path"] = str(manifest_path)
        result["manifest_path"] = str(manifest_path)
        result["result"] = summary
        return to_jsonable(result)

    def simulate_batch(
        self,
        limit: int = 50,
        n_simulations: int = 500,
        random_state: int | None = 42,
    ) -> dict[str, Any]:
        """Run Monte Carlo over the top scored objects and save reports/manifests."""
        run_id = create_run_id("simulation")
        started_at = utc_now_manifest()
        warnings: list[str] = []
        errors: list[str] = []
        df = self.load_risk_scores()
        if df.empty:
            errors.append("Risk scores not found. Run: python -m neo_ange.cli risk build")
            result = self._result("failed", {}, {}, warnings, errors)
            result["manifest_path"] = str(
                self._save_manifest(run_id, started_at, result, {"limit": limit})
            )
            return result

        batch = self.engine.simulate_batch(
            df,
            limit=limit,
            n_simulations=n_simulations,
            random_state=random_state,
        )
        warnings.extend(batch.get("warnings", []))
        results = batch.get("results", [])
        outputs = self.report_writer.save_outputs(results)
        metrics = batch.get("summary", {})
        status = "partial_success" if warnings else "success"
        result = self._result(status, outputs, metrics, warnings, errors)
        result["results"] = results
        manifest_path = self._save_manifest(
            run_id,
            started_at,
            result,
            {
                "limit": limit,
                "n_simulations": n_simulations,
                "random_state": random_state,
            },
        )
        result["outputs"]["manifest_path"] = str(manifest_path)
        result["manifest_path"] = str(manifest_path)
        return to_jsonable(result)

    def status(self) -> dict[str, Any]:
        """Return simulation data/report availability."""
        latest_reports = _latest_paths(self.report_dir, ["*.json", "*.csv", "*.md"])
        latest_manifests = [
            str(path) for path in list_manifests("simulation", self.manifest_dir)[-5:]
        ]
        latest_manifest = load_latest_manifest("simulation", self.manifest_dir)
        row_count = 0
        if self.simulation_results_path.exists():
            row_count = int(len(pd.read_parquet(self.simulation_results_path)))
        return {
            "status": "ok",
            "risk_scores_available": not self.load_risk_scores().empty,
            "simulation_results_available": self.simulation_results_path.exists(),
            "simulation_results_path": str(self.simulation_results_path),
            "row_count": row_count,
            "latest_reports": [str(path) for path in latest_reports],
            "latest_manifests": latest_manifests,
            "latest_manifest_status": latest_manifest.get("status") if latest_manifest else None,
            "simulation_version": MONTE_CARLO_VERSION,
        }

    def latest_for_object(self, object_key: str) -> dict[str, Any] | None:
        """Return the latest saved simulation result for an object."""
        if not self.simulation_results_path.exists():
            return None
        df = pd.read_parquet(self.simulation_results_path)
        if df.empty or "object_key" not in df.columns:
            return None
        matches = df[df["object_key"].astype("string") == str(object_key)]
        if matches.empty:
            return None
        if "simulated_at_utc" in matches.columns:
            matches = matches.sort_values("simulated_at_utc")
        return to_jsonable(matches.iloc[-1].to_dict())

    def methodology(self) -> dict[str, Any]:
        """Return methodology report path and content."""
        path = self.report_dir / "monte_carlo_methodology.md"
        if not path.exists():
            path = self.report_writer.write_methodology()
        return {"path": str(path), "content": path.read_text(encoding="utf-8")}

    def _save_manifest(
        self,
        run_id: str,
        started_at: str,
        result: dict[str, Any],
        inputs: dict[str, Any],
    ) -> Path:
        manifest = RunManifest(
            run_id=run_id,
            run_type="simulation",
            started_at_utc=started_at,
            ended_at_utc=utc_now_manifest(),
            status=result["status"],
            inputs={
                "risk_scores_path": str(self.risk_scores_path),
                **inputs,
            },
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


def _find_object(df: pd.DataFrame, object_key: str) -> dict[str, Any] | None:
    lookup = str(object_key)
    for column in ["object_key", "spkid", "des", "full_name", "name"]:
        if column not in df.columns:
            continue
        matches = df[df[column].astype("string") == lookup]
        if not matches.empty:
            return matches.iloc[0].to_dict()
    return None


def _latest_paths(root: Path, patterns: list[str], limit: int = 5) -> list[Path]:
    if not root.exists():
        return []
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(path for path in root.glob(pattern) if path.is_file())
    return sorted(paths, key=lambda path: path.stat().st_mtime, reverse=True)[:limit]
