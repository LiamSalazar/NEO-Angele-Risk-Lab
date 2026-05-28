"""Build gold analytical feature datasets from silver Parquet tables."""

from __future__ import annotations

import json
from pathlib import Path

from pyspark.sql import Column, DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql import types as T

from neo_ange.etl.silver_transformers import (
    CAD_COLUMNS,
    INGESTION_EVENT_COLUMNS,
    SBDB_OBJECT_COLUMNS,
    SENTRY_OBJECT_COLUMNS,
    SENTRY_VI_COLUMNS,
)
from neo_ange.utils.paths import contains_files, to_spark_path

GOLD_FEATURE_COLUMNS: list[tuple[str, T.DataType]] = [
    ("object_key", T.StringType()),
    ("spkid", T.StringType()),
    ("des", T.StringType()),
    ("full_name", T.StringType()),
    ("name", T.StringType()),
    ("orbit_class_code", T.StringType()),
    ("orbit_class_name", T.StringType()),
    ("neo", T.BooleanType()),
    ("pha", T.BooleanType()),
    ("sentry_flag", T.BooleanType()),
    ("h", T.DoubleType()),
    ("diameter", T.DoubleType()),
    ("albedo", T.DoubleType()),
    ("e", T.DoubleType()),
    ("a", T.DoubleType()),
    ("q", T.DoubleType()),
    ("i", T.DoubleType()),
    ("om", T.DoubleType()),
    ("w", T.DoubleType()),
    ("ma", T.DoubleType()),
    ("n", T.DoubleType()),
    ("per", T.DoubleType()),
    ("ad", T.DoubleType()),
    ("moid", T.DoubleType()),
    ("moid_ld", T.DoubleType()),
    ("condition_code", T.StringType()),
    ("arc_length", T.DoubleType()),
    ("n_obs_used", T.IntegerType()),
    ("rms", T.DoubleType()),
    ("min_close_approach_dist", T.DoubleType()),
    ("min_close_approach_dist_min", T.DoubleType()),
    ("max_close_approach_v_rel", T.DoubleType()),
    ("next_close_approach_datetime", T.StringType()),
    ("close_approach_count", T.LongType()),
    ("sentry_ip", T.DoubleType()),
    ("sentry_ps_cum", T.DoubleType()),
    ("sentry_ps_max", T.DoubleType()),
    ("sentry_ts_max", T.DoubleType()),
    ("sentry_n_imp", T.IntegerType()),
    ("log_diameter", T.DoubleType()),
    ("inverse_moid", T.DoubleType()),
    ("inverse_min_distance", T.DoubleType()),
    ("relative_velocity_score", T.DoubleType()),
    ("observation_quality_score", T.DoubleType()),
    ("uncertainty_proxy_score", T.DoubleType()),
    ("size_proxy_score", T.DoubleType()),
    ("proximity_proxy_score", T.DoubleType()),
    ("sentry_presence_score", T.DoubleType()),
    ("feature_completeness_ratio", T.DoubleType()),
    ("built_at_utc", T.StringType()),
    ("source_availability_json", T.StringType()),
]


class GoldBuilder:
    """Build model-ready analytical features from available silver tables."""

    def __init__(
        self,
        spark: SparkSession,
        silver_root: str | Path = "data/silver",
        gold_root: str | Path = "data/gold",
    ) -> None:
        self.spark = spark
        self.silver_root = Path(silver_root)
        self.gold_root = Path(gold_root)

    def build_neo_risk_features(self) -> DataFrame:
        """Build the initial feature table for future ranking and simulation work."""
        availability = {
            "sbdb_objects": self._table_exists("sbdb_objects"),
            "close_approaches": self._table_exists("close_approaches"),
            "sentry_objects": self._table_exists("sentry_objects"),
            "sentry_virtual_impactors": self._table_exists("sentry_virtual_impactors"),
        }

        base = self._build_base_objects(availability)
        if len(base.take(1)) == 0:
            return _empty_gold_df(self.spark)

        with_cad = self._join_close_approaches(base, availability["close_approaches"])
        with_sentry = self._join_sentry(with_cad, availability["sentry_objects"])
        featured = self._add_derived_features(
            with_sentry,
            source_availability_json=json.dumps(availability, sort_keys=True),
        )
        return _cast_to_gold_schema(featured)

    def _build_base_objects(self, availability: dict[str, bool]) -> DataFrame:
        if availability["sbdb_objects"]:
            objects = self._read_table("sbdb_objects")
            return (
                objects.select(
                    F.coalesce(
                        F.col("spkid").cast("string"),
                        F.col("pdes").cast("string"),
                        F.col("full_name").cast("string"),
                    ).alias("object_key"),
                    F.col("spkid").cast("string").alias("spkid"),
                    F.col("pdes").cast("string").alias("des"),
                    F.col("full_name").cast("string").alias("full_name"),
                    F.col("name").cast("string").alias("name"),
                    F.col("orbit_class_code").cast("string").alias("orbit_class_code"),
                    F.col("orbit_class_name").cast("string").alias("orbit_class_name"),
                    F.col("neo").cast("boolean").alias("neo"),
                    F.col("pha").cast("boolean").alias("pha"),
                    F.col("h").cast("double").alias("h"),
                    F.col("diameter").cast("double").alias("diameter"),
                    F.col("albedo").cast("double").alias("albedo"),
                    F.col("e").cast("double").alias("e"),
                    F.col("a").cast("double").alias("a"),
                    F.col("q").cast("double").alias("q"),
                    F.col("i").cast("double").alias("i"),
                    F.col("om").cast("double").alias("om"),
                    F.col("w").cast("double").alias("w"),
                    F.col("ma").cast("double").alias("ma"),
                    F.col("n").cast("double").alias("n"),
                    F.col("per").cast("double").alias("per"),
                    F.col("ad").cast("double").alias("ad"),
                    F.col("moid").cast("double").alias("moid"),
                    F.col("moid_ld").cast("double").alias("moid_ld"),
                    F.col("condition_code").cast("string").alias("condition_code"),
                    F.col("arc_length").cast("double").alias("arc_length"),
                    F.col("n_obs_used").cast("int").alias("n_obs_used"),
                    F.col("rms").cast("double").alias("rms"),
                )
                .where(F.col("object_key").isNotNull())
                .dropDuplicates(["object_key"])
            )

        if availability["sentry_objects"]:
            sentry = self._read_table("sentry_objects")
            return (
                sentry.select(
                    F.coalesce(F.col("spk"), F.col("des"), F.col("fullname")).alias("object_key"),
                    F.col("spk").cast("string").alias("spkid"),
                    F.col("des").cast("string").alias("des"),
                    F.col("fullname").cast("string").alias("full_name"),
                    F.lit(None).cast("string").alias("name"),
                    F.lit(None).cast("string").alias("orbit_class_code"),
                    F.lit(None).cast("string").alias("orbit_class_name"),
                    F.lit(None).cast("boolean").alias("neo"),
                    F.lit(None).cast("boolean").alias("pha"),
                    F.col("h").cast("double").alias("h"),
                    F.col("diameter").cast("double").alias("diameter"),
                    *[_null_double(name) for name in ORBITAL_BASE_COLUMNS],
                    F.lit(None).cast("string").alias("condition_code"),
                    F.lit(None).cast("double").alias("arc_length"),
                    F.lit(None).cast("int").alias("n_obs_used"),
                    F.lit(None).cast("double").alias("rms"),
                )
                .where(F.col("object_key").isNotNull())
                .dropDuplicates(["object_key"])
            )

        if availability["close_approaches"]:
            approaches = self._read_table("close_approaches")
            return (
                approaches.select(
                    F.coalesce(F.col("des"), F.col("fullname")).alias("object_key"),
                    F.lit(None).cast("string").alias("spkid"),
                    F.col("des").cast("string").alias("des"),
                    F.col("fullname").cast("string").alias("full_name"),
                    F.lit(None).cast("string").alias("name"),
                    F.lit(None).cast("string").alias("orbit_class_code"),
                    F.lit(None).cast("string").alias("orbit_class_name"),
                    F.lit(None).cast("boolean").alias("neo"),
                    F.lit(None).cast("boolean").alias("pha"),
                    F.col("h").cast("double").alias("h"),
                    F.col("diameter").cast("double").alias("diameter"),
                    *[_null_double(name) for name in ORBITAL_BASE_COLUMNS],
                    F.lit(None).cast("string").alias("condition_code"),
                    F.lit(None).cast("double").alias("arc_length"),
                    F.lit(None).cast("int").alias("n_obs_used"),
                    F.lit(None).cast("double").alias("rms"),
                )
                .where(F.col("object_key").isNotNull())
                .dropDuplicates(["object_key"])
            )

        return _empty_base_df(self.spark)

    def _join_close_approaches(self, base: DataFrame, available: bool) -> DataFrame:
        if not available:
            return base.select("*", *[_null_double_or_string(name) for name in CAD_AGG_COLUMNS])

        approaches = self._read_table("close_approaches")
        cad = approaches.groupBy("des").agg(
            F.min("dist").cast("double").alias("min_close_approach_dist"),
            F.min("dist_min").cast("double").alias("min_close_approach_dist_min"),
            F.max("v_rel").cast("double").alias("max_close_approach_v_rel"),
            F.min("close_approach_datetime").cast("string").alias("next_close_approach_datetime"),
            F.count(F.lit(1)).cast("long").alias("close_approach_count"),
        )
        return base.join(cad, on="des", how="left")

    def _join_sentry(self, base: DataFrame, available: bool) -> DataFrame:
        if not available:
            return base.select("*", *[_null_sentry_col(name) for name in SENTRY_AGG_COLUMNS])

        sentry = self._read_table("sentry_objects")
        aggregated = sentry.groupBy("des", "spk").agg(
            F.max("ip").cast("double").alias("sentry_ip"),
            F.max("ps_cum").cast("double").alias("sentry_ps_cum"),
            F.max("ps_max").cast("double").alias("sentry_ps_max"),
            F.max("ts_max").cast("double").alias("sentry_ts_max"),
            F.max("n_imp").cast("int").alias("sentry_n_imp"),
        )
        joined = base.join(
            aggregated,
            (base.des == aggregated.des) | (base.spkid == aggregated.spk),
            "left",
        )
        return joined.drop(aggregated.des).drop(aggregated.spk)

    def _add_derived_features(self, df: DataFrame, source_availability_json: str) -> DataFrame:
        with_flags = df.withColumn("sentry_flag", F.col("sentry_ip").isNotNull())

        log_diameter = F.when(F.col("diameter") > 0, F.log1p(F.col("diameter")))
        inverse_moid = F.when(F.col("moid") >= 0, F.lit(1.0) / (F.lit(1.0) + F.col("moid")))
        inverse_min_distance = F.when(
            F.col("min_close_approach_dist") >= 0,
            F.lit(1.0) / (F.lit(1.0) + F.col("min_close_approach_dist")),
        )
        velocity_score = _bounded(F.col("max_close_approach_v_rel") / F.lit(50.0))
        observations = _bounded(F.log1p(F.coalesce(F.col("n_obs_used"), F.lit(0))) / F.lit(9.21))
        arc = _bounded(F.log1p(F.coalesce(F.col("arc_length"), F.lit(0.0))) / F.lit(10.5))
        rms_quality = F.when(
            F.col("rms").isNotNull(), F.lit(1.0) / (F.lit(1.0) + F.col("rms"))
        ).otherwise(F.lit(0.0))
        observation_quality = _bounded(
            observations * F.lit(0.45) + arc * F.lit(0.45) + rms_quality * F.lit(0.10)
        )
        uncertainty = _bounded(
            F.coalesce(F.col("condition_code").cast("double"), F.lit(9.0)) / F.lit(9.0)
        )
        size_from_diameter = F.when(
            F.col("diameter") > 0,
            _bounded(F.log1p(F.col("diameter")) / F.lit(2.4)),
        )
        size_from_h = F.when(
            F.col("h").isNotNull(), _bounded((F.lit(30.0) - F.col("h")) / F.lit(15.0))
        )
        size_proxy = F.coalesce(size_from_diameter, size_from_h, F.lit(0.0))
        proximity = F.greatest(
            F.coalesce(inverse_min_distance, F.lit(0.0)),
            F.coalesce(inverse_moid, F.lit(0.0)),
        )
        completeness = _feature_completeness(
            [
                "h",
                "diameter",
                "e",
                "a",
                "q",
                "i",
                "moid",
                "min_close_approach_dist",
                "max_close_approach_v_rel",
                "sentry_ip",
                "condition_code",
                "arc_length",
                "n_obs_used",
                "rms",
            ]
        )

        return (
            with_flags.withColumn("log_diameter", log_diameter)
            .withColumn("inverse_moid", inverse_moid)
            .withColumn("inverse_min_distance", inverse_min_distance)
            .withColumn("relative_velocity_score", F.coalesce(velocity_score, F.lit(0.0)))
            .withColumn("observation_quality_score", observation_quality)
            .withColumn("uncertainty_proxy_score", uncertainty)
            .withColumn("size_proxy_score", size_proxy)
            .withColumn("proximity_proxy_score", proximity)
            .withColumn(
                "sentry_presence_score",
                F.when(F.col("sentry_flag"), F.lit(1.0)).otherwise(F.lit(0.0)),
            )
            .withColumn("feature_completeness_ratio", completeness)
            .withColumn(
                "built_at_utc", F.date_format(F.current_timestamp(), "yyyy-MM-dd'T'HH:mm:ss'Z'")
            )
            .withColumn("source_availability_json", F.lit(source_availability_json))
        )

    def _read_table(self, table_name: str) -> DataFrame:
        try:
            return self.spark.read.parquet(to_spark_path(self.silver_root / table_name))
        except Exception as exc:
            if not _is_windows_hadoop_native_io_error(exc):
                raise
            return _read_parquet_with_pyarrow(
                self.spark,
                self.silver_root / table_name,
                SILVER_SCHEMAS.get(table_name),
            )

    def _table_exists(self, table_name: str) -> bool:
        return contains_files(self.silver_root / table_name, "*.parquet")


ORBITAL_BASE_COLUMNS = [
    "albedo",
    "e",
    "a",
    "q",
    "i",
    "om",
    "w",
    "ma",
    "n",
    "per",
    "ad",
    "moid",
    "moid_ld",
]

CAD_AGG_COLUMNS: dict[str, T.DataType] = {
    "min_close_approach_dist": T.DoubleType(),
    "min_close_approach_dist_min": T.DoubleType(),
    "max_close_approach_v_rel": T.DoubleType(),
    "next_close_approach_datetime": T.StringType(),
    "close_approach_count": T.LongType(),
}

SENTRY_AGG_COLUMNS: dict[str, T.DataType] = {
    "sentry_ip": T.DoubleType(),
    "sentry_ps_cum": T.DoubleType(),
    "sentry_ps_max": T.DoubleType(),
    "sentry_ts_max": T.DoubleType(),
    "sentry_n_imp": T.IntegerType(),
}

SILVER_SCHEMAS: dict[str, list[tuple[str, T.DataType]]] = {
    "sbdb_objects": SBDB_OBJECT_COLUMNS,
    "close_approaches": CAD_COLUMNS,
    "sentry_objects": SENTRY_OBJECT_COLUMNS,
    "sentry_virtual_impactors": SENTRY_VI_COLUMNS,
    "ingestion_events": INGESTION_EVENT_COLUMNS,
}


def _empty_gold_df(spark: SparkSession) -> DataFrame:
    return spark.createDataFrame(
        [],
        T.StructType([T.StructField(name, dtype, True) for name, dtype in GOLD_FEATURE_COLUMNS]),
    )


def _empty_base_df(spark: SparkSession) -> DataFrame:
    base_columns = GOLD_FEATURE_COLUMNS[:29]
    return spark.createDataFrame(
        [],
        T.StructType([T.StructField(name, dtype, True) for name, dtype in base_columns]),
    )


def _cast_to_gold_schema(df: DataFrame) -> DataFrame:
    return df.select(*(F.col(name).cast(dtype).alias(name) for name, dtype in GOLD_FEATURE_COLUMNS))


def _null_double(name: str) -> Column:
    return F.lit(None).cast("double").alias(name)


def _null_double_or_string(name: str) -> Column:
    return F.lit(None).cast(CAD_AGG_COLUMNS[name]).alias(name)


def _null_sentry_col(name: str) -> Column:
    return F.lit(None).cast(SENTRY_AGG_COLUMNS[name]).alias(name)


def _bounded(value: Column) -> Column:
    return F.least(F.greatest(value.cast("double"), F.lit(0.0)), F.lit(1.0))


def _feature_completeness(columns: list[str]) -> Column:
    present = sum(
        F.when(F.col(column).isNotNull(), F.lit(1.0)).otherwise(F.lit(0.0)) for column in columns
    )
    return present / F.lit(float(len(columns)))


def _is_windows_hadoop_native_io_error(exc: Exception) -> bool:
    text = str(exc)
    return (
        "NativeIO$Windows" in text
        or "winutils" in text
        or "HADOOP_HOME" in text
        or "hadoop.home.dir" in text
    )


def _read_parquet_with_pyarrow(
    spark: SparkSession,
    table_path: Path,
    schema_columns: list[tuple[str, T.DataType]] | None,
) -> DataFrame:
    import pyarrow as pa
    import pyarrow.parquet as pq

    parquet_files = sorted(table_path.glob("*.parquet"))
    if not parquet_files:
        schema = T.StructType(
            [T.StructField(name, dtype, True) for name, dtype in schema_columns or []]
        )
        return spark.createDataFrame([], schema)

    arrow_table = pa.concat_tables([pq.read_table(path) for path in parquet_files])
    pdf = arrow_table.to_pandas()
    schema = None
    if schema_columns is not None:
        schema = T.StructType([T.StructField(name, dtype, True) for name, dtype in schema_columns])
    return spark.createDataFrame(pdf, schema=schema, verifySchema=False)
