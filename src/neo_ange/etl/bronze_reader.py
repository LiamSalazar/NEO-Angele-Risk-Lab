"""Read bronze JSON wrappers into Spark DataFrames."""

from __future__ import annotations

from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql import types as T

from neo_ange.utils.paths import to_spark_path


class BronzeSourceNotFoundError(FileNotFoundError):
    """Raised when a requested bronze source has no JSON files."""


class BronzeReader:
    """Read date-partitioned bronze wrappers produced by the ingestion layer."""

    def __init__(self, spark: SparkSession, bronze_root: str | Path = "data/bronze") -> None:
        self.spark = spark
        self.bronze_root = Path(bronze_root)

    def read_source(self, source: str) -> DataFrame:
        """Read one bronze source preserving wrapper metadata and file path lineage."""
        files = self._source_files(source)
        if not files:
            message = (
                f"Bronze source '{source}' is not available under "
                f"{self.bronze_root}. Run ingestion first or choose another source."
            )
            raise BronzeSourceNotFoundError(message)

        spark_paths = [to_spark_path(path) for path in files]
        df = (
            self.spark.read.option("multiLine", "true")
            .json(spark_paths)
            .withColumn("bronze_file_path", F.input_file_name())
            .withColumn(
                "ingest_date",
                F.regexp_extract(F.col("bronze_file_path"), r"ingest_date=([^/\\]+)", 1),
            )
        )
        if _has_field(df, "metadata") and not _has_field(df, "metadata.query_params"):
            df = df.withColumn(
                "metadata",
                F.col("metadata").withField(
                    "query_params",
                    F.create_map().cast("map<string,string>"),
                ),
            )
        return df

    def read_sbdb_object(self) -> DataFrame:
        return self.read_source("sbdb_object")

    def read_cad(self) -> DataFrame:
        return self.read_source("cad")

    def read_sentry(self) -> DataFrame:
        return self.read_source("sentry")

    def read_sbdb_query(self) -> DataFrame:
        return self.read_source("sbdb_query")

    def source_exists(self, source: str) -> bool:
        return bool(self._source_files(source))

    def list_available_sources(self) -> list[str]:
        if not self.bronze_root.exists():
            return []
        return sorted(
            child.name
            for child in self.bronze_root.iterdir()
            if child.is_dir() and any(child.rglob("*.json"))
        )

    def _source_files(self, source: str) -> list[Path]:
        source_dir = self.bronze_root / source
        if not source_dir.exists():
            return []
        return sorted(path for path in source_dir.rglob("*.json") if path.is_file())


def _has_field(df: DataFrame, path: str) -> bool:
    data_type: T.DataType = df.schema
    for part in path.split("."):
        if not isinstance(data_type, T.StructType):
            return False
        field = next((field for field in data_type.fields if field.name == part), None)
        if field is None:
            return False
        data_type = field.dataType
    return True
