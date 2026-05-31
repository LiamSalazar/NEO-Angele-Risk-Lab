"""Build user-facing analytical findings from persisted project artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from neo_ange.findings.schemas import finding
from neo_ange.utils.serialization import to_jsonable, write_json

RISK_COMPONENTS = {
    "physical_risk_component": "physical size",
    "orbital_risk_component": "orbital proximity",
    "approach_risk_component": "close-approach context",
    "sentry_risk_component": "Sentry signal",
    "uncertainty_risk_component": "orbital uncertainty",
    "data_quality_component": "data completeness",
}


class FindingsBuilder:
    """Generate concise findings for the app and report folders."""

    def __init__(
        self,
        gold_root: str | Path = "data/gold",
        reports_root: str | Path = "reports",
    ) -> None:
        self.gold_root = Path(gold_root)
        self.reports_root = Path(reports_root)
        self.report_dir = self.reports_root / "findings"

    def build_all(self, write: bool = True) -> dict[str, Any]:
        """Build and optionally persist all findings groups."""
        risk_df = _read_parquet(self.gold_root / "risk_scores" / "risk_scores.parquet")
        if risk_df.empty:
            risk_df = _read_parquet(self.gold_root / "risk_scores")
        gold_df = _read_parquet(self.gold_root / "neo_risk_features")
        feature_df = risk_df if not risk_df.empty else gold_df
        simulation_df = _read_parquet(
            self.gold_root / "simulation_results" / "monte_carlo_results.parquet"
        )
        orbital_df = _read_parquet(
            self.gold_root / "orbital_simulation" / "orbital_monte_carlo_results.parquet"
        )
        nodes_df = _read_parquet(self.gold_root / "gnn_graph" / "nodes.parquet")
        edges_df = _read_parquet(self.gold_root / "gnn_graph" / "edges.parquet")
        model_summary = _read_json(
            self.reports_root / "model_evidence" / "model_evidence_summary.json"
        )

        groups = {
            "dataset_findings": build_dataset_findings(feature_df),
            "risk_findings": build_risk_findings(risk_df),
            "score_simulation_findings": build_score_simulation_findings(simulation_df),
            "orbital_simulation_findings": build_orbital_findings(orbital_df),
            "graph_findings": build_graph_findings(nodes_df, edges_df),
            "model_evidence_findings": build_model_findings(model_summary),
            "object_findings_sample": build_object_findings_sample(
                risk_df, simulation_df, orbital_df, edges_df, nodes_df
            ),
        }
        summary_findings = [
            *groups["dataset_findings"][:2],
            *groups["risk_findings"][:3],
            *groups["score_simulation_findings"][:2],
            *groups["orbital_simulation_findings"][:2],
            *groups["graph_findings"][:2],
            *groups["model_evidence_findings"][:2],
        ]
        payload = {
            "status": "success" if summary_findings else "missing_data",
            "summary": {
                "finding_count": sum(
                    len(value) for key, value in groups.items() if key != "object_findings_sample"
                ),
                "dataset_rows": int(len(feature_df)),
                "risk_rows": int(len(risk_df)),
                "score_simulation_rows": int(len(simulation_df)),
                "orbital_simulation_rows": int(len(orbital_df)),
                "graph_nodes": int(len(nodes_df)),
                "graph_edges": int(len(edges_df)),
            },
            "findings": summary_findings,
            **groups,
        }
        if write:
            self.write_outputs(payload)
        return to_jsonable(payload)

    def status(self) -> dict[str, Any]:
        """Return report availability without rebuilding."""
        summary_path = self.report_dir / "findings_summary.json"
        payload = _read_json(summary_path)
        return {
            "status": payload.get("status", "missing_data") if payload else "missing_data",
            "summary_path": str(summary_path),
            "report_dir": str(self.report_dir),
            "finding_count": payload.get("summary", {}).get("finding_count", 0) if payload else 0,
        }

    def read_group(self, group_name: str) -> dict[str, Any]:
        """Read one generated finding group, rebuilding if absent."""
        mapping = {
            "summary": "findings_summary.json",
            "risk": "risk_findings.json",
            "score_simulation": "score_simulation_findings.json",
            "orbital_simulation": "orbital_simulation_findings.json",
            "orbital_graph": "graph_findings.json",
            "model_evidence": "model_evidence_findings.json",
            "object_sample": "object_findings_sample.json",
        }
        filename = mapping[group_name]
        path = self.report_dir / filename
        if not path.exists():
            self.build_all(write=True)
        return _read_json(path) or {"status": "missing_data", "findings": []}

    def object_findings(self, object_key: str) -> dict[str, Any]:
        """Build lightweight object-specific findings from the current artifacts."""
        risk_df = _read_parquet(self.gold_root / "risk_scores" / "risk_scores.parquet")
        row = _find_row(risk_df, object_key)
        if row is None:
            return {
                "status": "not_found",
                "object_key": object_key,
                "findings": [],
                "message": f"Object '{object_key}' was not found in risk scores.",
            }
        simulation_df = _read_parquet(
            self.gold_root / "simulation_results" / "monte_carlo_results.parquet"
        )
        orbital_df = _read_parquet(
            self.gold_root / "orbital_simulation" / "orbital_monte_carlo_results.parquet"
        )
        rows = []
        rows.append(_object_risk_finding(row))
        sim = _find_row(simulation_df, object_key)
        if sim is not None:
            rows.append(_object_score_simulation_finding(sim))
        orbital = _find_row(orbital_df, object_key)
        if orbital is not None:
            rows.append(_object_orbital_simulation_finding(orbital))
        return {"status": "success", "object_key": object_key, "findings": rows}

    def write_outputs(self, payload: dict[str, Any]) -> dict[str, str]:
        """Persist findings JSON and markdown files."""
        self.report_dir.mkdir(parents=True, exist_ok=True)
        outputs = {
            "findings_summary_json": str(
                write_json(
                    {
                        "status": payload["status"],
                        "summary": payload["summary"],
                        "findings": payload["findings"],
                    },
                    self.report_dir / "findings_summary.json",
                )
            ),
            "findings_summary_markdown": str(
                _write_markdown(
                    self.report_dir / "findings_summary.md",
                    "Analytical Findings Summary",
                    payload["findings"],
                    payload["summary"],
                )
            ),
            "risk_findings": str(
                write_json(
                    {"status": payload["status"], "findings": payload["risk_findings"]},
                    self.report_dir / "risk_findings.json",
                )
            ),
            "model_evidence_findings": str(
                write_json(
                    {
                        "status": payload["status"],
                        "findings": payload["model_evidence_findings"],
                    },
                    self.report_dir / "model_evidence_findings.json",
                )
            ),
            "graph_findings": str(
                write_json(
                    {"status": payload["status"], "findings": payload["graph_findings"]},
                    self.report_dir / "graph_findings.json",
                )
            ),
            "score_simulation_findings": str(
                write_json(
                    {
                        "status": payload["status"],
                        "findings": payload["score_simulation_findings"],
                    },
                    self.report_dir / "score_simulation_findings.json",
                )
            ),
            "orbital_simulation_findings": str(
                write_json(
                    {
                        "status": payload["status"],
                        "findings": payload["orbital_simulation_findings"],
                    },
                    self.report_dir / "orbital_simulation_findings.json",
                )
            ),
            "object_findings_sample": str(
                write_json(
                    {
                        "status": payload["status"],
                        "findings": payload["object_findings_sample"],
                    },
                    self.report_dir / "object_findings_sample.json",
                )
            ),
        }
        return outputs


def build_dataset_findings(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Generate findings about coverage and label distribution."""
    if df.empty:
        return [
            finding(
                "Dataset artifacts are not available yet",
                "No gold or risk-score rows were found for analytical findings.",
                "The findings builder could not read data/gold/neo_risk_features or risk scores.",
                importance="high",
                source_module="dataset",
                caveat="Run ETL and risk scoring before drawing dataset conclusions.",
            )
        ]
    rows = int(len(df))
    pha = _bool_count(df, "pha")
    sentry = _bool_count(df, "sentry_flag")
    physical_coverage = _coverage_ratio(df, ["diameter", "h", "albedo"])
    close_approach_coverage = _coverage_ratio(
        df, ["min_close_approach_dist", "close_approach_count"]
    )
    findings = [
        finding(
            "The current observatory dataset is analyzable",
            (
                f"The active dataset contains {rows:,} objects, with {pha['true']:,} PHA "
                f"labels and {pha['false']:,} non-PHA labels."
            ),
            "Counts are computed from the active gold/risk-score table.",
            importance="high",
            source_module="dataset",
            values={"objects": rows, "pha": pha},
        ),
        finding(
            "Sentry signal is limited to a small subset",
            (
                f"{sentry['true']:,} of {rows:,} objects carry a Sentry signal in the "
                "current dataset."
            ),
            "Sentry count is derived from the sentry_flag field.",
            importance="medium",
            source_module="dataset",
            values={"sentry_flag_true": sentry["true"], "objects": rows},
            caveat="Sentry fields are sparse and should not be interpreted as complete alerting.",
        ),
        finding(
            "Physical coverage is useful but incomplete",
            (
                f"At least one core physical field is available for "
                f"{physical_coverage:.1%} of objects."
            ),
            "Coverage checks diameter, absolute magnitude H and albedo.",
            importance="medium",
            source_module="dataset",
            values={"physical_coverage_ratio": physical_coverage},
        ),
        finding(
            "Close-approach context is present for part of the dataset",
            (
                f"Close-approach fields are populated for {close_approach_coverage:.1%} "
                "of the active objects."
            ),
            "Coverage checks minimum close-approach distance and approach counts.",
            importance="medium",
            source_module="dataset",
            values={"close_approach_coverage_ratio": close_approach_coverage},
        ),
    ]
    return findings


def build_risk_findings(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Generate findings about risk-score distribution and drivers."""
    if df.empty:
        return []
    score = pd.to_numeric(df.get("risk_score_0_100"), errors="coerce")
    category_counts = _value_counts(df, "risk_category")
    top = df.sort_values("risk_score_0_100", ascending=False).head(20)
    top_object = top.iloc[0].to_dict() if not top.empty else {}
    drivers = _dominant_drivers(top)
    elevated_count = int(
        df["risk_category"].astype("string").isin(["elevated", "high", "critical"]).sum()
    )
    most_common_category = (
        max(category_counts, key=category_counts.get) if category_counts else "unknown"
    )
    return [
        finding(
            "Most objects concentrate in moderate priority",
            (
                f"The largest risk category is {most_common_category}; "
                f"{category_counts.get(most_common_category, 0):,} objects fall there."
            ),
            "Risk categories are counted from the current risk_scores table.",
            importance="high",
            source_module="risk",
            values={"category_counts": category_counts},
        ),
        finding(
            "Elevated priority objects are a focused review set",
            (
                f"{elevated_count:,} objects are currently elevated or above, keeping "
                "the highest-priority review list compact."
            ),
            "Elevated objects are risk_category in elevated, high or critical.",
            related_objects=_object_keys(top.head(10)),
            importance="high",
            source_module="risk",
            values={"elevated_or_above": elevated_count},
        ),
        finding(
            "Top-ranked objects are driven by physical and orbital factors",
            (
                "Among the highest-ranked objects, physical size and orbital proximity "
                "are the dominant components."
            ),
            "Dominant components are counted across the top 20 rows by risk_score_0_100.",
            related_objects=_object_keys(top.head(10)),
            importance="high",
            source_module="risk",
            values={"dominant_drivers_top_20": drivers},
        ),
        finding(
            "The current top object is review-worthy within this experimental score",
            (
                f"{top_object.get('object_key', 'n/a')} has the highest current score "
                f"({float(top_object.get('risk_score_0_100', 0)):.1f}/100)."
            ),
            "Top object is selected by descending risk_score_0_100.",
            related_objects=[str(top_object.get("object_key"))] if top_object else [],
            importance="high",
            source_module="risk",
            values={
                "score_mean": _nullable_float(score.mean()),
                "score_median": _nullable_float(score.median()),
                "score_max": _nullable_float(score.max()),
            },
            caveat="The score is an analytical priority score, not an official impact probability.",
        ),
    ]


def build_score_simulation_findings(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Generate findings about Monte Carlo score-stability outputs."""
    if df.empty:
        return [
            finding(
                "Score simulations have not been generated for the current run",
                "No saved score Monte Carlo rows were found.",
                "Expected data/gold/simulation_results/monte_carlo_results.parquet.",
                importance="medium",
                source_module="score_simulation",
                caveat="Run python -m neo_ange.cli simulate batch --limit 100 --n-simulations 500.",
            )
        ]
    shift = pd.to_numeric(df.get("category_shift_probability"), errors="coerce")
    p95 = pd.to_numeric(df.get("p95_score"), errors="coerce")
    stable = int((shift.fillna(0) <= 0.2).sum())
    unstable = df.sort_values("category_shift_probability", ascending=False).head(5)
    high_p95 = df.sort_values("p95_score", ascending=False).head(5)
    return [
        finding(
            "Most simulated top objects retain their priority band",
            (
                f"{stable:,} of {len(df):,} simulated objects have category-shift "
                "probability at or below 20%."
            ),
            "Category-shift probability is read from score Monte Carlo results.",
            related_objects=_object_keys(df.loc[shift.fillna(1) <= 0.2].head(5)),
            importance="medium",
            source_module="score_simulation",
            values={"stable_count": stable, "simulation_rows": int(len(df))},
        ),
        finding(
            "Some objects show score sensitivity near category thresholds",
            (
                "The highest shift-probability objects should be inspected before "
                "treating their category as stable."
            ),
            "Objects are ranked by category_shift_probability.",
            related_objects=_object_keys(unstable),
            importance="medium",
            source_module="score_simulation",
            values={
                "max_category_shift_probability": _nullable_float(shift.max()),
                "max_p95_score": _nullable_float(p95.max()),
            },
        ),
        finding(
            "Highest simulated p95 scores remain below critical levels",
            (
                "Current score simulations do not produce critical-priority p95 values "
                "in the saved batch."
            ),
            "The finding checks p95_score in saved score Monte Carlo output.",
            related_objects=_object_keys(high_p95),
            importance="medium",
            source_module="score_simulation",
            values={"max_p95_score": _nullable_float(p95.max())},
        ),
    ]


def build_orbital_findings(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Generate findings from approximate orbital simulation outputs."""
    if df.empty:
        return [
            finding(
                "Orbital scenario simulations are pending",
                "No approximate orbital Monte Carlo results were found yet.",
                "Expected data/gold/orbital_simulation/orbital_monte_carlo_results.parquet.",
                importance="medium",
                source_module="orbital_simulation",
                caveat="Run python -m neo_ange.cli orbital-sim batch --limit 50.",
            )
        ]
    category_counts = _value_counts(df, "scenario_category")
    uncertain = df.sort_values("dispersion_index", ascending=False).head(5)
    close = df.sort_values("simulated_min_distance_p05_au", ascending=True).head(5)
    return [
        finding(
            "Approximate orbital scenarios are available for priority objects",
            f"{len(df):,} objects have saved orbital perturbation results.",
            "Rows are read from orbital_monte_carlo_results.parquet.",
            importance="high",
            source_module="orbital_simulation",
            values={
                "rows": int(
                    len(df),
                ),
                "scenario_categories": category_counts,
            },
        ),
        finding(
            "Orbital uncertainty varies across the priority set",
            (
                "Objects with the highest dispersion index deserve closer review in "
                "the orbital simulation view."
            ),
            "Objects are ranked by dispersion_index.",
            related_objects=_object_keys(uncertain),
            importance="medium",
            source_module="orbital_simulation",
            values={"scenario_categories": category_counts},
        ),
        finding(
            "Small p05 distance scenarios identify objects worth inspection",
            "The lowest simulated p05 minimum-distance rows are useful as an inspection queue.",
            "Objects are ranked by simulated_min_distance_p05_au.",
            related_objects=_object_keys(close),
            importance="medium",
            source_module="orbital_simulation",
            values={
                "lowest_p05_au": _nullable_float(
                    pd.to_numeric(df.get("simulated_min_distance_p05_au"), errors="coerce").min()
                )
            },
            caveat="The orbital simulation is approximate and uses available orbital elements.",
        ),
    ]


def build_graph_findings(nodes: pd.DataFrame, edges: pd.DataFrame) -> list[dict[str, Any]]:
    """Generate findings from orbital graph artifacts."""
    if nodes.empty:
        return [
            finding(
                "Orbital graph artifacts are pending",
                "The graph has not been exported or contains no nodes.",
                "Expected data/gold/gnn_graph/nodes.parquet.",
                importance="medium",
                source_module="orbital_graph",
            )
        ]
    density = _graph_density(len(nodes), len(edges))
    return [
        finding(
            "The orbital graph forms an analytical neighborhood",
            f"The graph contains {len(nodes):,} nodes and {len(edges):,} similarity edges.",
            "Nodes and edges are counted from exported graph Parquet files.",
            importance="high",
            source_module="orbital_graph",
            values={"nodes": int(len(nodes)), "edges": int(len(edges)), "density": density},
        ),
        finding(
            "Graph neighborhoods support object-level comparison",
            (
                "Nearest-neighbor links can be used to inspect orbitally similar "
                "objects around a selected NEO."
            ),
            (
                "Edges are kNN orbital-similarity links built from scaled orbital and "
                "risk-context features."
            ),
            related_objects=_object_keys(nodes.head(5)),
            importance="medium",
            source_module="orbital_graph",
            values={"edge_type": _value_counts(edges, "edge_type")},
        ),
    ]


def build_model_findings(summary: dict[str, Any]) -> list[dict[str, Any]]:
    """Generate findings from model-evidence outputs."""
    if not summary:
        return [
            finding(
                "Model evidence has not been generated yet",
                "No model evidence summary is available.",
                "Expected reports/model_evidence/model_evidence_summary.json.",
                importance="medium",
                source_module="model_evidence",
                caveat="Run python -m neo_ange.cli findings build or model-evidence generation.",
            )
        ]
    defensible = summary.get("best_defensible_model") or {}
    leakage = summary.get("leakage_sensitive_models", [])
    disagreements = summary.get("disagreement_count", 0)
    rows = [
        finding(
            "Best defensible evidence avoids definition-heavy leakage",
            (
                f"{defensible.get('model_name', 'n/a')} on "
                f"{defensible.get('feature_set', 'n/a')} is the current defensible "
                "model-evidence view."
            ),
            (
                "The evidence builder excludes definition-heavy feature sets from the "
                "best defensible pick."
            ),
            importance="high",
            source_module="model_evidence",
            values={"best_defensible_model": defensible},
        ),
        finding(
            "Model disagreements create an inspection queue",
            f"{disagreements:,} object/model rows are flagged in disagreement outputs.",
            (
                "Disagreements compare high-confidence predictions against observed "
                "labels or model families."
            ),
            importance="medium",
            source_module="model_evidence",
            values={"disagreement_count": disagreements},
        ),
    ]
    if leakage:
        rows.append(
            finding(
                "Some high-performing model views are leakage-sensitive",
                (
                    "Definition-heavy or score-derived feature sets are retained as "
                    "diagnostics, not primary evidence."
                ),
                (
                    "Leakage-sensitive models are identified from feature-set names "
                    "and model-card metadata."
                ),
                importance="medium",
                source_module="model_evidence",
                values={"leakage_sensitive_models": leakage[:5]},
            )
        )
    return rows


def build_object_findings_sample(
    risk_df: pd.DataFrame,
    simulation_df: pd.DataFrame,
    orbital_df: pd.DataFrame,
    edges_df: pd.DataFrame,
    nodes_df: pd.DataFrame,
) -> list[dict[str, Any]]:
    """Build sample object-level findings for top-ranked objects."""
    if risk_df.empty:
        return []
    top = risk_df.sort_values("risk_score_0_100", ascending=False).head(10)
    findings = []
    for _, row in top.iterrows():
        payload = _object_risk_finding(row.to_dict())
        object_key = str(row.get("object_key"))
        sim = _find_row(simulation_df, object_key)
        orbital = _find_row(orbital_df, object_key)
        neighbor_count = _neighbor_count(object_key, nodes_df, edges_df)
        payload["values"]["graph_neighbor_count"] = neighbor_count
        if sim is not None:
            payload["values"]["category_shift_probability"] = sim.get("category_shift_probability")
        if orbital is not None:
            payload["values"]["orbital_scenario_category"] = orbital.get("scenario_category")
        findings.append(payload)
    return findings


def _object_risk_finding(row: dict[str, Any]) -> dict[str, Any]:
    key = str(row.get("object_key"))
    driver = _dominant_driver(row)
    score = float(row.get("risk_score_0_100") or 0)
    return finding(
        f"{key} is prioritized mainly by {driver}",
        f"{key} has score {score:.1f}/100 in category {row.get('risk_category', 'unknown')}.",
        "Dominant driver is the largest weighted risk component for this object.",
        related_objects=[key],
        importance="high" if score >= 40 else "medium",
        source_module="object",
        values={
            "risk_score_0_100": score,
            "risk_category": row.get("risk_category"),
            "dominant_driver": driver,
        },
    )


def _object_score_simulation_finding(row: dict[str, Any]) -> dict[str, Any]:
    key = str(row.get("object_key"))
    shift = float(row.get("category_shift_probability") or 0)
    return finding(
        f"{key} score stability has been simulated",
        f"The saved score simulation has category-shift probability {shift:.1%}.",
        "Score stability comes from the Monte Carlo score-simulation output.",
        related_objects=[key],
        importance="medium",
        source_module="score_simulation",
        values={"category_shift_probability": shift, "p95_score": row.get("p95_score")},
    )


def _object_orbital_simulation_finding(row: dict[str, Any]) -> dict[str, Any]:
    key = str(row.get("object_key"))
    return finding(
        f"{key} has approximate orbital scenario results",
        f"The orbital scenario category is {row.get('scenario_category', 'unknown')}.",
        "Scenario category is derived from clone dispersion and p05 minimum distance.",
        related_objects=[key],
        importance="medium",
        source_module="orbital_simulation",
        values={
            "scenario_category": row.get("scenario_category"),
            "dispersion_index": row.get("dispersion_index"),
            "simulated_min_distance_p05_au": row.get("simulated_min_distance_p05_au"),
        },
        caveat="Approximate orbital scenario analysis based on available orbital elements.",
    )


def _read_parquet(path: Path) -> pd.DataFrame:
    if path.is_file():
        return pd.read_parquet(path)
    if path.is_dir() and any(path.glob("*.parquet")):
        return pd.read_parquet(path)
    return pd.DataFrame()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_markdown(
    path: Path,
    title: str,
    findings: list[dict[str, Any]],
    summary: dict[str, Any],
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {title}",
        "",
        "## Summary",
        "",
        *[f"- {key}: {value}" for key, value in summary.items()],
        "",
        "## Findings",
        "",
    ]
    if not findings:
        lines.append("- No findings were generated.")
    for item in findings:
        lines.extend(
            [
                f"### {item['title']}",
                "",
                item["short_text"],
                "",
                f"- Basis: {item['technical_basis']}",
                f"- Importance: {item['importance']}",
                f"- Source: {item['source_module']}",
            ]
        )
        if item.get("related_objects"):
            lines.append(f"- Related objects: {', '.join(item['related_objects'])}")
        if item.get("caveat"):
            lines.append(f"- Caveat: {item['caveat']}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _bool_count(df: pd.DataFrame, column: str) -> dict[str, int]:
    if column not in df.columns:
        return {"true": 0, "false": 0, "unknown": int(len(df))}
    normalized = df[column].astype("string").str.lower()
    true_mask = normalized.isin(["true", "1", "yes", "y", "t"])
    false_mask = normalized.isin(["false", "0", "no", "n", "f"])
    return {
        "true": int(true_mask.sum()),
        "false": int(false_mask.sum()),
        "unknown": int((~true_mask & ~false_mask).sum()),
    }


def _coverage_ratio(df: pd.DataFrame, columns: list[str]) -> float:
    available = [column for column in columns if column in df.columns]
    if df.empty or not available:
        return 0.0
    return float(df[available].notna().any(axis=1).mean())


def _value_counts(df: pd.DataFrame, column: str) -> dict[str, int]:
    if df.empty or column not in df.columns:
        return {}
    return {str(key): int(value) for key, value in df[column].value_counts(dropna=False).items()}


def _dominant_drivers(df: pd.DataFrame) -> dict[str, int]:
    if df.empty:
        return {}
    counts: dict[str, int] = {}
    for _, row in df.iterrows():
        label = _dominant_driver(row.to_dict())
        counts[label] = counts.get(label, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: item[1], reverse=True))


def _dominant_driver(row: dict[str, Any]) -> str:
    values = {}
    for column, label in RISK_COMPONENTS.items():
        try:
            values[label] = float(row.get(column) or 0)
        except (TypeError, ValueError):
            values[label] = 0.0
    return max(values, key=values.get) if values else "unknown"


def _object_keys(df: pd.DataFrame) -> list[str]:
    if df.empty or "object_key" not in df.columns:
        return []
    return [str(value) for value in df["object_key"].dropna().astype("string").head(10).tolist()]


def _nullable_float(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(result):
        return None
    return result


def _graph_density(nodes: int, edges: int) -> float:
    if nodes <= 1:
        return 0.0
    return float((2 * edges) / (nodes * (nodes - 1)))


def _find_row(df: pd.DataFrame, object_key: str) -> dict[str, Any] | None:
    if df.empty or "object_key" not in df.columns:
        return None
    matches = df[df["object_key"].astype("string") == str(object_key)]
    if matches.empty:
        return None
    return to_jsonable(matches.iloc[-1].to_dict())


def _neighbor_count(object_key: str, nodes: pd.DataFrame, edges: pd.DataFrame) -> int:
    if nodes.empty or edges.empty or "object_key" not in nodes.columns:
        return 0
    matches = nodes[nodes["object_key"].astype("string") == str(object_key)]
    if matches.empty:
        return 0
    node_id = int(matches.iloc[0]["node_id"])
    return int(((edges["source"] == node_id) | (edges["target"] == node_id)).sum())
