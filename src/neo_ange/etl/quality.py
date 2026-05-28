"""Data quality checks for silver and gold datasets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from neo_ange.utils.paths import ensure_directory
from neo_ange.utils.time import utc_timestamp_compact


class DataQualityChecker:
    """Run JSON-serializable quality checks without making warnings fatal."""

    def check_required_columns(self, df: DataFrame, required_columns: list[str]) -> dict[str, Any]:
        missing = [column for column in required_columns if column not in df.columns]
        return {
            "name": "required_columns",
            "status": "fail" if missing else "pass",
            "required_columns": required_columns,
            "missing_columns": missing,
        }

    def check_non_empty(self, df: DataFrame, dataset_name: str) -> dict[str, Any]:
        row_count = df.count()
        return {
            "name": "non_empty",
            "dataset": dataset_name,
            "status": "fail" if row_count == 0 else "pass",
            "row_count": row_count,
        }

    def check_null_ratio(self, df: DataFrame, columns: list[str]) -> dict[str, Any]:
        row_count = df.count()
        ratios: dict[str, float | None] = {}
        existing_columns = [column for column in columns if column in df.columns]
        for column in columns:
            if column not in df.columns:
                ratios[column] = None
            elif row_count == 0:
                ratios[column] = None
        if row_count > 0 and existing_columns:
            aggregate_row = df.agg(
                *(
                    F.sum(F.when(F.col(column).isNull(), F.lit(1)).otherwise(F.lit(0))).alias(
                        column
                    )
                    for column in existing_columns
                )
            ).first()
            for column in existing_columns:
                ratios[column] = aggregate_row[column] / row_count
        status = (
            "warn" if any(value is None or value > 0.95 for value in ratios.values()) else "pass"
        )
        return {"name": "null_ratio", "status": status, "row_count": row_count, "ratios": ratios}

    def check_duplicate_keys(self, df: DataFrame, key_columns: list[str]) -> dict[str, Any]:
        missing = [column for column in key_columns if column not in df.columns]
        if missing:
            return {
                "name": "duplicate_keys",
                "status": "fail",
                "key_columns": key_columns,
                "missing_columns": missing,
            }
        duplicate_count = df.groupBy(*key_columns).count().where(F.col("count") > 1).count()
        return {
            "name": "duplicate_keys",
            "status": "warn" if duplicate_count > 0 else "pass",
            "key_columns": key_columns,
            "duplicate_key_count": duplicate_count,
        }

    def check_numeric_ranges(
        self,
        df: DataFrame,
        rules: dict[str, tuple[float | None, float | None]],
    ) -> dict[str, Any]:
        checks_by_column: dict[str, dict[str, Any]] = {}
        aggregate_expressions = []
        for column, (minimum, maximum) in rules.items():
            if column not in df.columns:
                checks_by_column[column] = {
                    "column": column,
                    "status": "warn",
                    "missing": True,
                    "out_of_range_count": None,
                }
                continue
            condition = F.lit(False)
            if minimum is not None:
                condition = condition | (F.col(column) < F.lit(minimum))
            if maximum is not None:
                condition = condition | (F.col(column) > F.lit(maximum))
            aggregate_expressions.append(
                F.sum(
                    F.when(F.col(column).isNotNull() & condition, F.lit(1)).otherwise(F.lit(0))
                ).alias(column)
            )
            checks_by_column[column] = {"column": column, "min": minimum, "max": maximum}
        aggregate_row = df.agg(*aggregate_expressions).first() if aggregate_expressions else None
        for column, check in checks_by_column.items():
            if check.get("missing"):
                continue
            out_of_range_count = aggregate_row[column] if aggregate_row is not None else 0
            check["status"] = "warn" if out_of_range_count else "pass"
            check["out_of_range_count"] = out_of_range_count
        checks = [checks_by_column[column] for column in rules]
        status = "warn" if any(check["status"] == "warn" for check in checks) else "pass"
        return {"name": "numeric_ranges", "status": status, "checks": checks}

    def run_gold_quality_checks(self, df: DataFrame) -> dict[str, Any]:
        checks = [
            self.check_required_columns(
                df,
                [
                    "object_key",
                    "neo",
                    "pha",
                    "sentry_flag",
                    "feature_completeness_ratio",
                    "built_at_utc",
                    "source_availability_json",
                ],
            ),
            self.check_non_empty(df, "neo_risk_features"),
            self.check_null_ratio(
                df,
                [
                    "object_key",
                    "h",
                    "diameter",
                    "moid",
                    "min_close_approach_dist",
                    "sentry_ip",
                ],
            ),
            self.check_duplicate_keys(df, ["object_key"]),
            self.check_numeric_ranges(
                df,
                {
                    "feature_completeness_ratio": (0.0, 1.0),
                    "relative_velocity_score": (0.0, 1.0),
                    "observation_quality_score": (0.0, 1.0),
                    "uncertainty_proxy_score": (0.0, 1.0),
                    "size_proxy_score": (0.0, 1.0),
                    "proximity_proxy_score": (0.0, 1.0),
                    "sentry_presence_score": (0.0, 1.0),
                    "diameter": (0.0, None),
                    "moid": (0.0, None),
                },
            ),
        ]
        status = "pass"
        if any(check["status"] == "fail" for check in checks):
            status = "fail"
        elif any(check["status"] == "warn" for check in checks):
            status = "warn"
        return {"dataset": "neo_risk_features", "status": status, "checks": checks}

    def write_quality_report(self, report: dict[str, Any], gold_root: str | Path) -> Path:
        reports_dir = ensure_directory(Path(gold_root) / "quality_reports")
        output_path = reports_dir / f"neo_risk_features_quality_{utc_timestamp_compact()}.json"
        output_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        return output_path
