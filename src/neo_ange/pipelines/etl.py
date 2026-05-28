"""ETL orchestration for bronze, silver, and gold layers."""

from __future__ import annotations

from functools import reduce
from pathlib import Path
from typing import Any

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from neo_ange.etl.bronze_reader import BronzeReader, BronzeSourceNotFoundError
from neo_ange.etl.gold_builder import GoldBuilder
from neo_ange.etl.quality import DataQualityChecker
from neo_ange.etl.silver_transformers import SilverTransformers
from neo_ange.etl.writers import ParquetTableWriter
from neo_ange.manifests.run_manifest import (
    RunManifest,
    create_run_id,
    save_manifest,
    utc_now_manifest,
)
from neo_ange.services.gold_storage import GoldStorage
from neo_ange.services.silver_storage import SilverStorage
from neo_ange.utils.paths import contains_files

SUPPORTED_SOURCES = {"sbdb_object", "cad", "sentry", "sbdb_query"}
DEFAULT_SOURCES = ["sbdb_object", "cad", "sentry", "sbdb_query"]


class ETLPipeline:
    """Coordinate Spark bronze-to-silver transforms and gold feature building."""

    def __init__(
        self,
        spark: SparkSession,
        bronze_root: str | Path = "data/bronze",
        silver_root: str | Path = "data/silver",
        gold_root: str | Path = "data/gold",
    ) -> None:
        self.spark = spark
        self.bronze_root = Path(bronze_root)
        self.silver_root = Path(silver_root)
        self.gold_root = Path(gold_root)
        self.reader = BronzeReader(spark, self.bronze_root)
        self.transformers = SilverTransformers(spark)
        self.writer = ParquetTableWriter()
        self.silver_storage = SilverStorage(self.silver_root)
        self.gold_storage = GoldStorage(self.gold_root)
        self.quality = DataQualityChecker()

    def run_bronze_to_silver(self, source: str | None = None) -> dict[str, Any]:
        warnings: list[str] = []
        errors: list[str] = []
        outputs: dict[str, Any] = {}
        ingestion_event_frames: list[DataFrame] = []

        sources = self._resolve_sources(source, warnings, errors)
        for current_source in sources:
            try:
                bronze_df = self.reader.read_source(current_source)
            except BronzeSourceNotFoundError as exc:
                message = str(exc)
                if source is None:
                    warnings.append(message)
                else:
                    errors.append(message)
                continue

            ingestion_event_frames.append(self.transformers.transform_ingestion_events(bronze_df))
            source_outputs = self._process_source(current_source, bronze_df, warnings)
            outputs.update(source_outputs)

        if ingestion_event_frames:
            events_df = reduce(
                lambda left, right: left.unionByName(right, allowMissingColumns=True),
                ingestion_event_frames,
            )
            outputs["ingestion_events"] = self.writer.write(
                events_df,
                self.silver_storage.table_path("ingestion_events"),
            )

        if source is None:
            for expected in DEFAULT_SOURCES:
                if expected not in sources and expected != "sbdb_query":
                    warnings.append(f"Optional bronze source '{expected}' is not available.")

        status = _status_from_outputs(outputs, warnings, errors)
        return {
            "status": status,
            "silver_outputs": outputs,
            "warnings": warnings,
            "errors": errors,
        }

    def run_gold(
        self,
        min_rows_for_ml: int = 100,
        min_positive_class_count: int = 5,
        target: str = "pha",
    ) -> dict[str, Any]:
        warnings: list[str] = []
        errors: list[str] = []
        builder = GoldBuilder(self.spark, self.silver_root, self.gold_root)
        features_df = builder.build_neo_risk_features().cache()
        row_count = features_df.count()
        column_count = len(features_df.columns)
        volume_metrics = _gold_volume_metrics(features_df, target=target)
        warnings.extend(
            _gold_volume_warnings(
                row_count=row_count,
                target=target,
                min_rows_for_ml=min_rows_for_ml,
                min_positive_class_count=min_positive_class_count,
                volume_metrics=volume_metrics,
            )
        )
        missing_optional_sources = _missing_optional_sources(self.silver_root)
        try:
            quality_report = self.quality.run_gold_quality_checks(features_df)
            report_path = self.quality.write_quality_report(quality_report, self.gold_root)

            output = self.writer.write(
                features_df,
                self.gold_storage.table_path("neo_risk_features"),
            )
        finally:
            features_df.unpersist()
        if output["status"] == "skipped_empty":
            errors.append("Gold dataset 'neo_risk_features' is empty.")
        if quality_report["status"] == "warn":
            warnings.append("Gold quality checks completed with warnings.")
        if quality_report["status"] == "fail":
            errors.append("Gold quality checks failed.")

        return {
            "status": "failed" if errors else ("partial_success" if warnings else "success"),
            "gold_outputs": {"neo_risk_features": output},
            "quality_report": str(report_path),
            "quality_status": quality_report["status"],
            "metrics": {
                "gold_row_count": row_count,
                "gold_column_count": column_count,
                "target": target,
                **volume_metrics,
                "missing_optional_sources": missing_optional_sources,
            },
            "warnings": warnings,
            "errors": errors,
        }

    def run_all(
        self,
        min_rows_for_ml: int = 100,
        min_positive_class_count: int = 5,
        target: str = "pha",
    ) -> dict[str, Any]:
        run_id = create_run_id("etl")
        started_at = utc_now_manifest()
        try:
            silver_result = self.run_bronze_to_silver()
            gold_result = self.run_gold(
                min_rows_for_ml=min_rows_for_ml,
                min_positive_class_count=min_positive_class_count,
                target=target,
            )
        except Exception as exc:
            result = {
                "status": "failed",
                "silver_outputs": {},
                "gold_outputs": {},
                "quality_report": None,
                "metrics": {},
                "warnings": [],
                "errors": [str(exc)],
            }
            manifest_path = self._save_run_all_manifest(
                run_id=run_id,
                started_at=started_at,
                result=result,
                inputs={
                    "min_rows_for_ml": min_rows_for_ml,
                    "min_positive_class_count": min_positive_class_count,
                    "target": target,
                },
            )
            result["manifest_path"] = str(manifest_path)
            return result

        warnings = [*silver_result.get("warnings", []), *gold_result.get("warnings", [])]
        errors = [*silver_result.get("errors", []), *gold_result.get("errors", [])]
        if errors:
            status = "failed" if not silver_result.get("silver_outputs") else "partial_success"
        elif warnings:
            status = "partial_success"
        else:
            status = "success"

        result = {
            "status": status,
            "silver_outputs": silver_result.get("silver_outputs", {}),
            "gold_outputs": gold_result.get("gold_outputs", {}),
            "quality_report": gold_result.get("quality_report"),
            "quality_status": gold_result.get("quality_status"),
            "metrics": {
                "silver_row_counts": _silver_row_counts(silver_result.get("silver_outputs", {})),
                **gold_result.get("metrics", {}),
                "quality_report_path": gold_result.get("quality_report"),
            },
            "warnings": warnings,
            "errors": errors,
        }
        manifest_path = self._save_run_all_manifest(
            run_id=run_id,
            started_at=started_at,
            result=result,
            inputs={
                "min_rows_for_ml": min_rows_for_ml,
                "min_positive_class_count": min_positive_class_count,
                "target": target,
            },
        )
        result["manifest_path"] = str(manifest_path)
        return result

    def _save_run_all_manifest(
        self,
        run_id: str,
        started_at: str,
        result: dict[str, Any],
        inputs: dict[str, Any],
    ) -> Path:
        manifest = RunManifest(
            run_id=run_id,
            run_type="etl",
            started_at_utc=started_at,
            ended_at_utc=utc_now_manifest(),
            status=result["status"],
            inputs={
                "bronze_root": str(self.bronze_root),
                "silver_root": str(self.silver_root),
                "gold_root": str(self.gold_root),
                **inputs,
            },
            outputs={
                "silver_outputs": result.get("silver_outputs", {}),
                "gold_outputs": result.get("gold_outputs", {}),
                "quality_report": result.get("quality_report"),
            },
            metrics=result.get("metrics", {}),
            warnings=result.get("warnings", []),
            errors=result.get("errors", []),
        )
        return save_manifest(manifest)

    def _resolve_sources(
        self,
        source: str | None,
        warnings: list[str],
        errors: list[str],
    ) -> list[str]:
        if source is not None:
            if source not in SUPPORTED_SOURCES:
                errors.append(
                    f"Unsupported source '{source}'. Expected one of: {sorted(SUPPORTED_SOURCES)}."
                )
                return []
            return [source]

        available = self.reader.list_available_sources()
        unsupported = [item for item in available if item not in SUPPORTED_SOURCES]
        for item in unsupported:
            warnings.append(f"Skipping unsupported bronze source '{item}'.")
        return [item for item in DEFAULT_SOURCES if item in available]

    def _process_source(
        self,
        source: str,
        bronze_df: DataFrame,
        warnings: list[str],
    ) -> dict[str, Any]:
        outputs: dict[str, Any] = {}
        if source == "sbdb_object":
            outputs["sbdb_objects"] = self.writer.write(
                self.transformers.transform_sbdb_objects(bronze_df),
                self.silver_storage.table_path("sbdb_objects"),
            )
        elif source == "cad":
            outputs["close_approaches"] = self.writer.write(
                self.transformers.transform_close_approaches(bronze_df),
                self.silver_storage.table_path("close_approaches"),
            )
        elif source == "sentry":
            outputs["sentry_objects"] = self.writer.write(
                self.transformers.transform_sentry_objects(bronze_df),
                self.silver_storage.table_path("sentry_objects"),
            )
            outputs["sentry_virtual_impactors"] = self.writer.write(
                self.transformers.transform_sentry_virtual_impactors(bronze_df),
                self.silver_storage.table_path("sentry_virtual_impactors"),
            )
            for table_name, output in outputs.items():
                if output["status"] == "skipped_empty":
                    warnings.append(f"No rows were produced for optional table '{table_name}'.")
        elif source == "sbdb_query":
            warnings.append(
                "Source 'sbdb_query' has no dedicated silver table in this milestone; "
                "its metadata is captured in silver_ingestion_events."
            )
        return outputs


def _status_from_outputs(
    outputs: dict[str, Any],
    warnings: list[str],
    errors: list[str],
) -> str:
    if errors:
        return "failed" if not outputs else "partial_success"
    if not outputs:
        return "failed"
    if warnings:
        return "partial_success"
    return "success"


def _silver_row_counts(outputs: dict[str, Any]) -> dict[str, int]:
    return {
        table_name: int(output.get("row_count", 0))
        for table_name, output in outputs.items()
        if isinstance(output, dict)
    }


def _missing_optional_sources(silver_root: Path) -> list[str]:
    optional_tables = [
        "close_approaches",
        "sentry_objects",
        "sentry_virtual_impactors",
    ]
    return [
        table_name
        for table_name in optional_tables
        if not contains_files(silver_root / table_name, "*.parquet")
    ]


def _gold_volume_metrics(features_df: DataFrame, target: str) -> dict[str, Any]:
    if target not in features_df.columns:
        return {
            "target_positive_count": 0,
            "target_negative_count": 0,
            "target_positive_rate": None,
            "target_missing_count": None,
        }
    aggregate = features_df.select(
        F.sum(F.when(F.col(target).cast("int") == 1, F.lit(1)).otherwise(F.lit(0))).alias(
            "positive"
        ),
        F.sum(F.when(F.col(target).cast("int") == 0, F.lit(1)).otherwise(F.lit(0))).alias(
            "negative"
        ),
        F.sum(F.when(F.col(target).isNull(), F.lit(1)).otherwise(F.lit(0))).alias("missing"),
    ).first()
    positive = int(aggregate["positive"] or 0)
    negative = int(aggregate["negative"] or 0)
    labeled = positive + negative
    return {
        "target_positive_count": positive,
        "target_negative_count": negative,
        "target_positive_rate": positive / labeled if labeled else None,
        "target_missing_count": int(aggregate["missing"] or 0),
    }


def _gold_volume_warnings(
    row_count: int,
    target: str,
    min_rows_for_ml: int,
    min_positive_class_count: int,
    volume_metrics: dict[str, Any],
) -> list[str]:
    warnings: list[str] = []
    if row_count < min_rows_for_ml:
        warnings.append(
            f"Gold dataset has {row_count} row(s); baseline ML expects at least "
            f"{min_rows_for_ml}."
        )
    positive_count = int(volume_metrics.get("target_positive_count") or 0)
    if positive_count < min_positive_class_count:
        warnings.append(
            f"Gold target '{target}' has {positive_count} positive row(s); baseline ML expects "
            f"at least {min_positive_class_count}."
        )
    if volume_metrics.get("target_missing_count") is None:
        warnings.append(f"Gold target '{target}' is missing.")
    return warnings
