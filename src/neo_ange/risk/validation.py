"""Validation reports for the deterministic Risk Priority Score."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from neo_ange.risk.schemas import COMPONENT_COLUMNS, DEFAULT_COMPONENT_WEIGHTS, RISK_SCORE_VERSION
from neo_ange.risk.scoring import RiskScorer
from neo_ange.simulation.schemas import PERTURBED_VARIABLES
from neo_ange.simulation.sensitivity import SensitivityAnalyzer
from neo_ange.utils.serialization import write_json

COMPONENT_FORMULAS: dict[str, dict[str, Any]] = {
    "physical_risk_component": {
        "variables": ["diameter", "h", "log_diameter", "size_proxy_score"],
        "formula": "weighted_available(log1p(diameter), inverse H scale, log_diameter, size proxy)",
        "range": [0, 1],
        "clipping": "component values are clipped to [0, 1]",
        "internal_weights": {
            "diameter_score": 0.35,
            "h_score": 0.30,
            "log_diameter_score": 0.15,
            "size_proxy_score": 0.20,
        },
        "justification": (
            "Larger inferred size and lower absolute magnitude increase review priority."
        ),
        "limitations": "Diameter coverage is sparse; H is a proxy, not a direct size measurement.",
    },
    "orbital_risk_component": {
        "variables": ["moid", "moid_ld", "inverse_moid", "q", "e", "i"],
        "formula": "weighted_available(inverse MOID scales, perihelion, eccentricity, inclination)",
        "range": [0, 1],
        "clipping": "component values are clipped to [0, 1]",
        "internal_weights": {
            "moid_score": 0.35,
            "moid_ld_score": 0.20,
            "inverse_moid_score": 0.15,
            "q_score": 0.10,
            "eccentricity_score": 0.12,
            "inclination_score": 0.08,
        },
        "justification": (
            "Lower MOID and more Earth-crossing orbital context increase review priority."
        ),
        "limitations": "This component does not propagate a dynamical orbit or impact probability.",
    },
    "approach_risk_component": {
        "variables": [
            "min_close_approach_dist",
            "min_close_approach_dist_min",
            "inverse_min_distance",
            "max_close_approach_v_rel",
            "relative_velocity_score",
            "close_approach_count",
        ],
        "formula": "weighted_available(close approach distance, velocity, and count scores)",
        "range": [0, 1],
        "clipping": "component values are clipped to [0, 1]",
        "internal_weights": {
            "distance_score": 0.28,
            "min_distance_score": 0.20,
            "inverse_distance_score": 0.14,
            "direct_velocity_score": 0.16,
            "stored_velocity_score": 0.12,
            "count_score": 0.10,
        },
        "justification": "Closer and faster documented approaches receive higher review priority.",
        "limitations": (
            "CAD coverage depends on the ingested window and is not a full ephemeris search."
        ),
    },
    "sentry_risk_component": {
        "variables": [
            "sentry_flag",
            "sentry_presence_score",
            "sentry_ip",
            "sentry_ps_cum",
            "sentry_ps_max",
            "sentry_ts_max",
            "sentry_n_imp",
        ],
        "formula": (
            "weighted_available(Sentry presence, impact probability, Palermo/Torino, VI count)"
        ),
        "range": [0, 1],
        "clipping": "probability and transformed score signals are clipped to [0, 1]",
        "internal_weights": {
            "flag_score": 0.20,
            "presence_score": 0.15,
            "ip_score": 0.25,
            "ps_cum_score": 0.13,
            "ps_max_score": 0.12,
            "ts_score": 0.10,
            "impact_count_score": 0.05,
        },
        "justification": "Sentry-listed objects are important secondary evidence for review.",
        "limitations": "Sentry absence is not proof of zero risk.",
    },
    "uncertainty_risk_component": {
        "variables": [
            "condition_code",
            "rms",
            "arc_length",
            "n_obs_used",
            "uncertainty_proxy_score",
        ],
        "formula": "weighted_available(condition code, RMS, short arc, low observation count)",
        "range": [0, 1],
        "clipping": "component values are clipped to [0, 1]",
        "internal_weights": {
            "condition_score": 0.28,
            "rms_score": 0.18,
            "short_arc_score": 0.22,
            "low_obs_score": 0.20,
            "proxy_score": 0.12,
        },
        "justification": "Poorer orbit-quality proxies increase review priority uncertainty.",
        "limitations": "This is a quality proxy, not a covariance-derived uncertainty metric.",
    },
    "data_quality_component": {
        "variables": ["feature_completeness_ratio", "arc_length", "n_obs_used"],
        "formula": "weighted_available(incompleteness, short arc, low observation count)",
        "range": [0, 1],
        "clipping": "component values are clipped to [0, 1]",
        "internal_weights": {
            "incompleteness_score": 0.50,
            "short_arc_score": 0.25,
            "low_obs_score": 0.25,
        },
        "justification": "Rows with weaker feature coverage are surfaced with a small moderator.",
        "limitations": "The component should not be interpreted as physical hazard.",
    },
}


class RiskValidationReporter:
    """Write formula, sensitivity, and ablation reports for risk scoring."""

    def __init__(self, report_dir: str | Path = "reports/risk") -> None:
        self.report_dir = Path(report_dir)

    def write_all(self, scored_df: pd.DataFrame) -> dict[str, str]:
        """Persist all risk validation artifacts."""
        self.report_dir.mkdir(parents=True, exist_ok=True)
        formulas_path = self.write_component_formulas()
        methodology_path = self.write_detailed_methodology()
        sensitivity_path, sensitivity_summary = self.write_component_sensitivity(scored_df)
        ablation_json, ablation_md = self.write_ablation(scored_df)
        return {
            "risk_component_formulas_json": str(formulas_path),
            "risk_score_methodology_detailed_md": str(methodology_path),
            "risk_component_sensitivity_csv": str(sensitivity_path),
            "risk_component_sensitivity_summary_json": str(sensitivity_summary),
            "risk_ablation_summary_json": str(ablation_json),
            "risk_ablation_summary_markdown": str(ablation_md),
        }

    def write_component_formulas(self) -> Path:
        """Write a machine-readable formula report."""
        return write_json(
            {
                "score_version": RISK_SCORE_VERSION,
                "component_weights": DEFAULT_COMPONENT_WEIGHTS,
                "components": COMPONENT_FORMULAS,
                "ranking_source": "Risk Priority Score",
                "calibration_status": "not_calibrated_against_impacts",
            },
            self.report_dir / "risk_component_formulas.json",
        )

    def write_detailed_methodology(self) -> Path:
        """Write a human-readable score methodology report."""
        path = self.report_dir / "risk_score_methodology_detailed.md"
        lines = [
            "# Risk Score Methodology Detailed",
            "",
            "The Risk Priority Score is deterministic and explainable. It ranks objects for "
            "project review; it does not predict impact probability and is not calibrated "
            "against real impacts.",
            "",
            f"Score version: `{RISK_SCORE_VERSION}`",
            "",
            "## Component weights",
            "",
            *[f"- `{name}`: {weight}" for name, weight in DEFAULT_COMPONENT_WEIGHTS.items()],
            "",
            "## Components",
            "",
        ]
        for name, payload in COMPONENT_FORMULAS.items():
            lines.extend(
                [
                    f"### {name}",
                    "",
                    f"- Variables: {', '.join(payload['variables'])}",
                    f"- Formula: {payload['formula']}",
                    f"- Range: {payload['range']}",
                    f"- Clipping: {payload['clipping']}",
                    f"- Justification: {payload['justification']}",
                    f"- Limitations: {payload['limitations']}",
                    "",
                ]
            )
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    def write_component_sensitivity(self, scored_df: pd.DataFrame) -> tuple[Path, Path]:
        """Write deterministic sensitivity rows for top scored objects."""
        rows: list[dict[str, Any]] = []
        if not scored_df.empty:
            source = (
                scored_df.sort_values("risk_score_0_100", ascending=False).head(100)
                if "risk_score_0_100" in scored_df.columns
                else scored_df.head(100)
            )
            analyzer = SensitivityAnalyzer(RiskScorer())
            for _, row in source.iterrows():
                object_key = _object_key(row)
                for item in analyzer.estimate_feature_sensitivity(
                    row,
                    variables=list(PERTURBED_VARIABLES),
                ):
                    rows.append({"object_key": object_key, **item})
        df = pd.DataFrame(rows)
        path = self.report_dir / "risk_component_sensitivity.csv"
        df.to_csv(path, index=False)
        summary = _sensitivity_summary(df)
        summary_path = write_json(
            summary, self.report_dir / "risk_component_sensitivity_summary.json"
        )
        return path, summary_path

    def write_ablation(self, scored_df: pd.DataFrame) -> tuple[Path, Path]:
        """Write component ablation effects using existing component columns."""
        summary = _ablation_summary(scored_df)
        json_path = write_json(summary, self.report_dir / "risk_ablation_summary.json")
        md_path = self.report_dir / "risk_ablation_summary.md"
        md_path.write_text(_render_ablation_markdown(summary), encoding="utf-8")
        return json_path, md_path


def _ablation_summary(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty or "risk_score_0_100" not in df.columns:
        return {"status": "missing_data", "row_count": 0}
    missing = [column for column in COMPONENT_COLUMNS if column not in df.columns]
    if missing:
        return {"status": "missing_components", "missing_components": missing, "row_count": len(df)}
    original = df.copy()
    original_rank = original["risk_score_0_100"].rank(ascending=False, method="min")
    top20_original = set(
        original.sort_values("risk_score_0_100", ascending=False).head(20)["object_key"]
    )
    ablations: dict[str, Any] = {}
    for removed in COMPONENT_COLUMNS:
        kept = [column for column in COMPONENT_COLUMNS if column != removed]
        kept_weight_sum = sum(DEFAULT_COMPONENT_WEIGHTS[column] for column in kept)
        weights = {column: DEFAULT_COMPONENT_WEIGHTS[column] / kept_weight_sum for column in kept}
        ablated_score = (
            sum(
                pd.to_numeric(original[column], errors="coerce").fillna(0.0) * weight
                for column, weight in weights.items()
            )
            * 100.0
        )
        ablated_rank = ablated_score.rank(ascending=False, method="min")
        rank_delta = (ablated_rank - original_rank).abs()
        top20_ablated = set(
            original.assign(_score=ablated_score)
            .sort_values("_score", ascending=False)
            .head(20)["object_key"]
        )
        ablations[removed] = {
            "spearman_rank_correlation": _float_or_none(
                original_rank.corr(ablated_rank, method="spearman")
            ),
            "top20_overlap": int(len(top20_original & top20_ablated)),
            "mean_absolute_score_delta": _float_or_none(
                (ablated_score - original["risk_score_0_100"]).abs().mean()
            ),
            "largest_rank_changes": _largest_rank_changes(original, rank_delta),
        }
    return {
        "status": "success",
        "row_count": int(len(df)),
        "score_version": RISK_SCORE_VERSION,
        "default_weights_changed": False,
        "ablations": ablations,
    }


def _sensitivity_summary(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {"status": "missing_data", "row_count": 0}
    grouped = df.groupby("variable")["absolute_effect"].mean().sort_values(ascending=False).head(10)
    unstable = (
        df.groupby("object_key")["absolute_effect"].max().sort_values(ascending=False).head(10)
    )
    return {
        "status": "success",
        "row_count": int(len(df)),
        "analysis_mode": "deterministic_sensitivity",
        "top_variables_by_mean_absolute_effect": {
            str(key): _float_or_none(value) for key, value in grouped.items()
        },
        "most_sensitive_objects": {
            str(key): _float_or_none(value) for key, value in unstable.items()
        },
    }


def _largest_rank_changes(
    df: pd.DataFrame, rank_delta: pd.Series, limit: int = 10
) -> list[dict[str, Any]]:
    rows = df.assign(_rank_delta=rank_delta).sort_values("_rank_delta", ascending=False).head(limit)
    return [
        {
            "object_key": str(row.get("object_key")),
            "rank_delta": _float_or_none(row.get("_rank_delta")),
            "risk_score_0_100": _float_or_none(row.get("risk_score_0_100")),
        }
        for _, row in rows.iterrows()
    ]


def _render_ablation_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Risk Score Ablation Summary",
        "",
        "Component ablation recomputes the score with one component removed and remaining "
        "weights renormalized. Default weights are not changed.",
        "",
    ]
    if summary.get("status") != "success":
        lines.append(f"Status: {summary.get('status')}")
        return "\n".join(lines)
    for component, payload in summary.get("ablations", {}).items():
        lines.extend(
            [
                f"## Without {component}",
                "",
                f"- Spearman rank correlation: {payload.get('spearman_rank_correlation')}",
                f"- Top 20 overlap: {payload.get('top20_overlap')}",
                f"- Mean absolute score delta: {payload.get('mean_absolute_score_delta')}",
                "",
            ]
        )
    return "\n".join(lines)


def _object_key(row: pd.Series) -> str:
    for column in ("object_key", "spkid", "des", "full_name", "name"):
        value = row.get(column)
        if value is not None and not pd.isna(value):
            return str(value)
    return "unknown-object"


def _float_or_none(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(result):
        return None
    return result
