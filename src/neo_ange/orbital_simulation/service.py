"""Service orchestration for approximate orbital Monte Carlo simulations."""

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
from neo_ange.orbital_simulation.monte_carlo import OrbitalMonteCarloEngine
from neo_ange.orbital_simulation.reporting import OrbitalSimulationReportWriter
from neo_ange.orbital_simulation.schemas import ORBITAL_SIMULATION_VERSION
from neo_ange.utils.paths import contains_files
from neo_ange.utils.serialization import to_jsonable


class OrbitalSimulationService:
    """Load risk rows, run approximate orbital simulations, and save reports."""

    def __init__(
        self,
        gold_root: str | Path = "data/gold",
        risk_scores_dir: str | Path | None = None,
        output_dir: str | Path | None = None,
        report_dir: str | Path = "reports/orbital_simulation",
        manifest_dir: str | Path = "reports/manifests",
        engine: OrbitalMonteCarloEngine | None = None,
    ) -> None:
        self.gold_root = Path(gold_root)
        self.risk_scores_dir = (
            Path(risk_scores_dir) if risk_scores_dir else self.gold_root / "risk_scores"
        )
        self.output_dir = Path(output_dir) if output_dir else self.gold_root / "orbital_simulation"
        self.report_dir = Path(report_dir)
        self.manifest_dir = Path(manifest_dir)
        self.engine = engine or OrbitalMonteCarloEngine()
        self.writer = OrbitalSimulationReportWriter(self.output_dir, self.report_dir)

    @property
    def results_path(self) -> Path:
        """Return main result table path."""
        return self.writer.results_path

    def load_source_rows(self) -> pd.DataFrame:
        """Load risk scores first, falling back to gold features."""
        risk_path = self.risk_scores_dir / "risk_scores.parquet"
        if risk_path.exists():
            return pd.read_parquet(risk_path)
        if contains_files(self.risk_scores_dir, "*.parquet"):
            return pd.read_parquet(self.risk_scores_dir)
        gold_path = self.gold_root / "neo_risk_features"
        if contains_files(gold_path, "*.parquet"):
            return pd.read_parquet(gold_path)
        return pd.DataFrame()

    def simulate_object(
        self,
        object_key: str,
        n_clones: int = 500,
        horizon_days: int = 3650,
        time_step_days: int = 10,
        random_state: int | None = 42,
    ) -> dict[str, Any]:
        """Run approximate orbital simulation for one object."""
        run_id = create_run_id("orbital_sim")
        started_at = utc_now_manifest()
        df = self.load_source_rows()
        if df.empty:
            return self._with_manifest(
                run_id,
                started_at,
                "failed",
                {},
                [],
                ["Risk or gold feature rows are missing."],
                {"object_key": object_key},
            )
        row = _find_object(df, object_key)
        if row is None:
            return self._with_manifest(
                run_id,
                started_at,
                "not_found",
                {},
                [],
                [f"Object '{object_key}' was not found."],
                {"object_key": object_key},
            )
        result = self.engine.simulate_object(
            row,
            n_clones=n_clones,
            horizon_days=horizon_days,
            time_step_days=time_step_days,
            random_state=random_state,
        )
        outputs = self.writer.save_outputs([result])
        payload = self._with_manifest(
            run_id,
            started_at,
            "success",
            outputs,
            result.get("warnings", []),
            [],
            {
                "object_key": object_key,
                "n_clones": n_clones,
                "horizon_days": horizon_days,
                "time_step_days": time_step_days,
            },
        )
        payload["result"] = result
        return to_jsonable(payload)

    def simulate_batch(
        self,
        limit: int = 50,
        n_clones: int = 300,
        horizon_days: int = 3650,
        time_step_days: int = 10,
        random_state: int | None = 42,
    ) -> dict[str, Any]:
        """Run approximate orbital simulation for top-ranked objects."""
        run_id = create_run_id("orbital_sim")
        started_at = utc_now_manifest()
        df = self.load_source_rows()
        if df.empty:
            return self._with_manifest(
                run_id,
                started_at,
                "failed",
                {},
                [],
                ["Risk or gold feature rows are missing."],
                {"limit": limit},
            )
        if "risk_score_0_100" in df.columns:
            batch = df.sort_values("risk_score_0_100", ascending=False).head(limit)
        else:
            batch = df.head(limit)
        results = []
        warnings = []
        for offset, (_, row) in enumerate(batch.iterrows()):
            result = self.engine.simulate_object(
                row.to_dict(),
                n_clones=n_clones,
                horizon_days=horizon_days,
                time_step_days=time_step_days,
                random_state=None if random_state is None else random_state + offset,
            )
            warnings.extend(result.get("warnings", []))
            results.append(result)
        outputs = self.writer.save_outputs(results)
        payload = self._with_manifest(
            run_id,
            started_at,
            "success",
            outputs,
            sorted(set(warnings)),
            [],
            {
                "limit": limit,
                "n_clones": n_clones,
                "horizon_days": horizon_days,
                "time_step_days": time_step_days,
            },
        )
        payload["results"] = [
            {key: value for key, value in result.items() if key != "distance_trace"}
            for result in results
        ]
        payload["metrics_summary"] = _read_json(self.report_dir / "orbital_simulation_summary.json")
        return to_jsonable(payload)

    def latest_for_object(self, object_key: str) -> dict[str, Any] | None:
        """Return latest saved result for one object."""
        if not self.results_path.exists():
            return None
        df = pd.read_parquet(self.results_path)
        row = _find_object(df, object_key)
        return to_jsonable(row) if row is not None else None

    def findings(self) -> dict[str, Any]:
        """Read generated orbital simulation findings."""
        path = self.report_dir / "orbital_scenario_findings.json"
        if not path.exists():
            return {"status": "missing_data", "findings": []}
        return _read_json(path)

    def status(self) -> dict[str, Any]:
        """Return orbital simulation availability."""
        row_count = 0
        if self.results_path.exists():
            row_count = int(len(pd.read_parquet(self.results_path)))
        latest_manifest = load_latest_manifest("orbital_sim", self.manifest_dir)
        return {
            "status": "ok",
            "source_rows_available": not self.load_source_rows().empty,
            "orbital_simulation_available": self.results_path.exists(),
            "orbital_simulation_results_path": str(self.results_path),
            "row_count": row_count,
            "latest_reports": (
                [
                    str(path)
                    for path in sorted(
                        self.report_dir.glob("*"),
                        key=lambda item: item.stat().st_mtime,
                        reverse=True,
                    )[:5]
                    if path.is_file()
                ]
                if self.report_dir.exists()
                else []
            ),
            "latest_manifests": [
                str(path) for path in list_manifests("orbital_sim", self.manifest_dir)[-5:]
            ],
            "latest_manifest_status": latest_manifest.get("status") if latest_manifest else None,
            "simulation_version": ORBITAL_SIMULATION_VERSION,
        }

    def _with_manifest(
        self,
        run_id: str,
        started_at: str,
        status: str,
        outputs: dict[str, Any],
        warnings: list[str],
        errors: list[str],
        inputs: dict[str, Any],
    ) -> dict[str, Any]:
        payload = {
            "status": status,
            "outputs": outputs,
            "warnings": warnings,
            "errors": errors,
        }
        manifest = RunManifest(
            run_id=run_id,
            run_type="orbital_sim",
            started_at_utc=started_at,
            ended_at_utc=utc_now_manifest(),
            status=status,
            inputs=inputs,
            outputs=outputs,
            metrics={},
            warnings=warnings,
            errors=errors,
        )
        manifest_path = save_manifest(manifest, output_dir=self.manifest_dir)
        payload["manifest_path"] = str(manifest_path)
        payload["outputs"]["manifest_path"] = str(manifest_path)
        return payload


def _find_object(df: pd.DataFrame, object_key: str) -> dict[str, Any] | None:
    if df.empty:
        return None
    lookup = str(object_key)
    for column in ["object_key", "spkid", "des", "full_name", "name"]:
        if column not in df.columns:
            continue
        matches = df[df[column].astype("string") == lookup]
        if not matches.empty:
            return matches.iloc[-1].to_dict()
    return None


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    import json

    return json.loads(path.read_text(encoding="utf-8"))
