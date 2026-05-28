"""ETL orchestration for bronze, silver, and gold layers."""

from __future__ import annotations

from functools import reduce
from pathlib import Path
from typing import Any

from pyspark.sql import DataFrame, SparkSession

from neo_ange.etl.bronze_reader import BronzeReader, BronzeSourceNotFoundError
from neo_ange.etl.gold_builder import GoldBuilder
from neo_ange.etl.quality import DataQualityChecker
from neo_ange.etl.silver_transformers import SilverTransformers
from neo_ange.etl.writers import ParquetTableWriter
from neo_ange.services.gold_storage import GoldStorage
from neo_ange.services.silver_storage import SilverStorage

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

    def run_gold(self) -> dict[str, Any]:
        warnings: list[str] = []
        errors: list[str] = []
        builder = GoldBuilder(self.spark, self.silver_root, self.gold_root)
        features_df = builder.build_neo_risk_features().cache()
        features_df.count()
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
            "warnings": warnings,
            "errors": errors,
        }

    def run_all(self) -> dict[str, Any]:
        silver_result = self.run_bronze_to_silver()
        gold_result = self.run_gold()

        warnings = [*silver_result.get("warnings", []), *gold_result.get("warnings", [])]
        errors = [*silver_result.get("errors", []), *gold_result.get("errors", [])]
        if errors:
            status = "failed" if not silver_result.get("silver_outputs") else "partial_success"
        elif warnings:
            status = "partial_success"
        else:
            status = "success"

        return {
            "status": status,
            "silver_outputs": silver_result.get("silver_outputs", {}),
            "gold_outputs": gold_result.get("gold_outputs", {}),
            "quality_report": gold_result.get("quality_report"),
            "warnings": warnings,
            "errors": errors,
        }

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
