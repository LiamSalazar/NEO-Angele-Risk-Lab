"""Silver-layer Spark transformations for NASA/JPL bronze payloads."""

from __future__ import annotations

from functools import reduce
from operator import or_

from pyspark.sql import Column, DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql import types as T

STRING = T.StringType()
DOUBLE = T.DoubleType()
INTEGER = T.IntegerType()
BOOLEAN = T.BooleanType()


SBDB_OBJECT_COLUMNS: list[tuple[str, T.DataType]] = [
    ("object_id", STRING),
    ("source", STRING),
    ("ingested_at_utc", STRING),
    ("spkid", STRING),
    ("full_name", STRING),
    ("pdes", STRING),
    ("name", STRING),
    ("prefix", STRING),
    ("orbit_id", STRING),
    ("neo", BOOLEAN),
    ("pha", BOOLEAN),
    ("kind", STRING),
    ("orbit_class_code", STRING),
    ("orbit_class_name", STRING),
    ("condition_code", STRING),
    ("orbit_solution_date", STRING),
    ("first_obs", STRING),
    ("last_obs", STRING),
    ("arc_length", DOUBLE),
    ("n_obs_used", INTEGER),
    ("rms", DOUBLE),
    ("h", DOUBLE),
    ("diameter", DOUBLE),
    ("albedo", DOUBLE),
    ("moid", DOUBLE),
    ("moid_ld", DOUBLE),
    ("e", DOUBLE),
    ("a", DOUBLE),
    ("q", DOUBLE),
    ("i", DOUBLE),
    ("om", DOUBLE),
    ("w", DOUBLE),
    ("ma", DOUBLE),
    ("n", DOUBLE),
    ("tp", DOUBLE),
    ("per", DOUBLE),
    ("ad", DOUBLE),
    ("raw_json", STRING),
]

CAD_COLUMNS: list[tuple[str, T.DataType]] = [
    ("source", STRING),
    ("ingested_at_utc", STRING),
    ("des", STRING),
    ("orbit_id", STRING),
    ("jd", DOUBLE),
    ("cd", STRING),
    ("close_approach_datetime", STRING),
    ("dist", DOUBLE),
    ("dist_min", DOUBLE),
    ("dist_max", DOUBLE),
    ("v_rel", DOUBLE),
    ("v_inf", DOUBLE),
    ("t_sigma_f", STRING),
    ("body", STRING),
    ("h", DOUBLE),
    ("diameter", DOUBLE),
    ("diameter_sigma", DOUBLE),
    ("fullname", STRING),
    ("raw_json", STRING),
]

SENTRY_OBJECT_COLUMNS: list[tuple[str, T.DataType]] = [
    ("source", STRING),
    ("ingested_at_utc", STRING),
    ("des", STRING),
    ("fullname", STRING),
    ("spk", STRING),
    ("h", DOUBLE),
    ("diameter", DOUBLE),
    ("ip", DOUBLE),
    ("ps_cum", DOUBLE),
    ("ps_max", DOUBLE),
    ("ts_max", DOUBLE),
    ("last_obs", STRING),
    ("n_imp", INTEGER),
    ("last_obs_jd", DOUBLE),
    ("raw_json", STRING),
]

SENTRY_VI_COLUMNS: list[tuple[str, T.DataType]] = [
    ("source", STRING),
    ("ingested_at_utc", STRING),
    ("des", STRING),
    ("fullname", STRING),
    ("spk", STRING),
    ("ip", DOUBLE),
    ("date", STRING),
    ("dist", DOUBLE),
    ("width", DOUBLE),
    ("sigma_imp", DOUBLE),
    ("ps", DOUBLE),
    ("ts", DOUBLE),
    ("energy", DOUBLE),
    ("vinf", DOUBLE),
    ("raw_json", STRING),
]

INGESTION_EVENT_COLUMNS: list[tuple[str, T.DataType]] = [
    ("source", STRING),
    ("ingested_at_utc", STRING),
    ("ingest_date", STRING),
    ("object_id", STRING),
    ("query_params_json", STRING),
    ("api_signature_version", STRING),
    ("bronze_file_path", STRING),
]


class SilverTransformers:
    """Normalize bronze wrappers into source-specific silver tables."""

    def __init__(self, spark: SparkSession) -> None:
        self.spark = spark

    def transform_sbdb_objects(self, bronze_df: DataFrame) -> DataFrame:
        moid = F.coalesce(
            _col(bronze_df, "data.orbit.moid", DOUBLE),
            _col(bronze_df, "data.orbit_defs.moid", DOUBLE),
        )
        moid_ld = F.coalesce(
            _col(bronze_df, "data.orbit.moid_ld", DOUBLE),
            _col(bronze_df, "data.orbit_defs.moid_ld", DOUBLE),
            F.when(moid > 0, moid * F.lit(389.174)),
        )

        selected = bronze_df.select(
            F.coalesce(
                _col(bronze_df, "metadata.object_id"),
                _col(bronze_df, "data.object.des"),
                _col(bronze_df, "data.object.spkid"),
            ).alias("object_id"),
            _source_col(bronze_df).alias("source"),
            _col(bronze_df, "metadata.ingested_at_utc").alias("ingested_at_utc"),
            _col(bronze_df, "data.object.spkid").alias("spkid"),
            _col(bronze_df, "data.object.fullname").alias("full_name"),
            _col(bronze_df, "data.object.des").alias("pdes"),
            F.coalesce(
                _col(bronze_df, "data.object.name"),
                _col(bronze_df, "data.object.shortname"),
            ).alias("name"),
            _col(bronze_df, "data.object.prefix").alias("prefix"),
            F.coalesce(
                _col(bronze_df, "data.object.orbit_id"),
                _col(bronze_df, "data.orbit.orbit_id"),
            ).alias("orbit_id"),
            _flag_to_bool(_col(bronze_df, "data.object.neo")).alias("neo"),
            _flag_to_bool(_col(bronze_df, "data.object.pha")).alias("pha"),
            _col(bronze_df, "data.object.kind").alias("kind"),
            _col(bronze_df, "data.object.orbit_class.code").alias("orbit_class_code"),
            F.coalesce(
                _col(bronze_df, "data.object.orbit_class.name"),
                _col(bronze_df, "data.object.orbit_class.description"),
            ).alias("orbit_class_name"),
            F.coalesce(
                _col(bronze_df, "data.orbit.condition_code"),
                _col(bronze_df, "data.orbit_defs.condition_code"),
            ).alias("condition_code"),
            F.coalesce(
                _col(bronze_df, "data.orbit.soln_date"),
                _col(bronze_df, "data.orbit_defs.soln_date"),
            ).alias("orbit_solution_date"),
            F.coalesce(
                _col(bronze_df, "data.orbit.first_obs"),
                _col(bronze_df, "data.orbit_defs.first_obs"),
            ).alias("first_obs"),
            F.coalesce(
                _col(bronze_df, "data.orbit.last_obs"),
                _col(bronze_df, "data.orbit_defs.last_obs"),
            ).alias("last_obs"),
            F.coalesce(
                _col(bronze_df, "data.orbit.data_arc", DOUBLE),
                _col(bronze_df, "data.orbit_defs.data_arc", DOUBLE),
            ).alias("arc_length"),
            F.coalesce(
                _col(bronze_df, "data.orbit.n_obs_used", INTEGER),
                _col(bronze_df, "data.orbit_defs.n_obs_used", INTEGER),
            ).alias("n_obs_used"),
            F.coalesce(
                _col(bronze_df, "data.orbit.rms", DOUBLE),
                _col(bronze_df, "data.orbit_defs.rms", DOUBLE),
            ).alias("rms"),
            F.coalesce(
                _array_value_by_name(bronze_df, "data.phys_par", "h", DOUBLE),
                _col(bronze_df, "data.object.h", DOUBLE),
            ).alias("h"),
            _array_value_by_name(bronze_df, "data.phys_par", "diameter", DOUBLE).alias("diameter"),
            _array_value_by_name(bronze_df, "data.phys_par", "albedo", DOUBLE).alias("albedo"),
            moid.alias("moid"),
            moid_ld.alias("moid_ld"),
            _orbital_element(bronze_df, "e").alias("e"),
            _orbital_element(bronze_df, "a").alias("a"),
            _orbital_element(bronze_df, "q").alias("q"),
            _orbital_element(bronze_df, "i").alias("i"),
            _orbital_element(bronze_df, "om").alias("om"),
            _orbital_element(bronze_df, "w").alias("w"),
            _orbital_element(bronze_df, "ma").alias("ma"),
            _orbital_element(bronze_df, "n").alias("n"),
            _orbital_element(bronze_df, "tp").alias("tp"),
            _orbital_element(bronze_df, "per").alias("per"),
            _orbital_element(bronze_df, "ad").alias("ad"),
            _json_col(bronze_df, "data").alias("raw_json"),
        )
        return _cast_to_schema(selected, SBDB_OBJECT_COLUMNS)

    def transform_close_approaches(self, bronze_df: DataFrame) -> DataFrame:
        if not (_has_field(bronze_df, "data.fields") and _has_field(bronze_df, "data.data")):
            return _empty_df(self.spark, CAD_COLUMNS)

        mapped = (
            bronze_df.withColumn("_row", F.explode_outer(F.col("data.data")))
            .where(F.col("_row").isNotNull())
            .withColumn("_field_map", F.map_from_arrays(F.col("data.fields"), F.col("_row")))
        )

        def field(name: str, data_type: T.DataType = STRING) -> Column:
            return F.element_at(F.col("_field_map"), F.lit(name)).cast(data_type)

        selected = mapped.select(
            _source_col(mapped).alias("source"),
            _col(mapped, "metadata.ingested_at_utc").alias("ingested_at_utc"),
            field("des").alias("des"),
            field("orbit_id").alias("orbit_id"),
            field("jd", DOUBLE).alias("jd"),
            field("cd").alias("cd"),
            field("cd").alias("close_approach_datetime"),
            field("dist", DOUBLE).alias("dist"),
            field("dist_min", DOUBLE).alias("dist_min"),
            field("dist_max", DOUBLE).alias("dist_max"),
            field("v_rel", DOUBLE).alias("v_rel"),
            field("v_inf", DOUBLE).alias("v_inf"),
            field("t_sigma_f").alias("t_sigma_f"),
            F.coalesce(field("body"), _col(mapped, "metadata.query_params.body")).alias("body"),
            field("h", DOUBLE).alias("h"),
            field("diameter", DOUBLE).alias("diameter"),
            field("diameter_sigma", DOUBLE).alias("diameter_sigma"),
            field("fullname").alias("fullname"),
            F.to_json(F.col("_field_map")).alias("raw_json"),
        )
        return _cast_to_schema(selected, CAD_COLUMNS)

    def transform_sentry_objects(self, bronze_df: DataFrame) -> DataFrame:
        if not _has_field(bronze_df, "data.data"):
            return _empty_df(self.spark, SENTRY_OBJECT_COLUMNS)
        if not any(
            _has_field(bronze_df, field)
            for field in ("data.data.ps_cum", "data.data.n_imp", "data.data.last_obs")
        ):
            return _empty_df(self.spark, SENTRY_OBJECT_COLUMNS)

        exploded = bronze_df.withColumn("_item", F.explode_outer(F.col("data.data"))).where(
            F.col("_item").isNotNull()
        )
        marker_conditions = [
            _col(exploded, "_item.ps_cum").isNotNull(),
            _col(exploded, "_item.n_imp").isNotNull(),
            _col(exploded, "_item.last_obs").isNotNull(),
        ]
        filtered = exploded.where(reduce(or_, marker_conditions))

        selected = filtered.select(
            _source_col(filtered).alias("source"),
            _col(filtered, "metadata.ingested_at_utc").alias("ingested_at_utc"),
            _col(filtered, "_item.des").alias("des"),
            _col(filtered, "_item.fullname").alias("fullname"),
            F.coalesce(_col(filtered, "_item.spk"), _col(filtered, "_item.spkid")).alias("spk"),
            _col(filtered, "_item.h", DOUBLE).alias("h"),
            _col(filtered, "_item.diameter", DOUBLE).alias("diameter"),
            _col(filtered, "_item.ip", DOUBLE).alias("ip"),
            _col(filtered, "_item.ps_cum", DOUBLE).alias("ps_cum"),
            _col(filtered, "_item.ps_max", DOUBLE).alias("ps_max"),
            _col(filtered, "_item.ts_max", DOUBLE).alias("ts_max"),
            _col(filtered, "_item.last_obs").alias("last_obs"),
            _col(filtered, "_item.n_imp", INTEGER).alias("n_imp"),
            _col(filtered, "_item.last_obs_jd", DOUBLE).alias("last_obs_jd"),
            F.to_json(F.col("_item")).alias("raw_json"),
        )
        return _cast_to_schema(selected, SENTRY_OBJECT_COLUMNS)

    def transform_sentry_virtual_impactors(self, bronze_df: DataFrame) -> DataFrame:
        if not _has_field(bronze_df, "data.data"):
            return _empty_df(self.spark, SENTRY_VI_COLUMNS)
        if not any(
            _has_field(bronze_df, field)
            for field in (
                "data.data.date",
                "data.data.ps",
                "data.data.sigma_vi",
                "data.data.energy",
            )
        ):
            return _empty_df(self.spark, SENTRY_VI_COLUMNS)

        exploded = bronze_df.withColumn("_item", F.explode_outer(F.col("data.data"))).where(
            F.col("_item").isNotNull()
        )
        marker_conditions = [
            _col(exploded, "_item.date").isNotNull(),
            _col(exploded, "_item.ps").isNotNull(),
            _col(exploded, "_item.sigma_vi").isNotNull(),
            _col(exploded, "_item.energy").isNotNull(),
        ]
        filtered = exploded.where(reduce(or_, marker_conditions))

        selected = filtered.select(
            _source_col(filtered).alias("source"),
            _col(filtered, "metadata.ingested_at_utc").alias("ingested_at_utc"),
            _col(filtered, "_item.des").alias("des"),
            _col(filtered, "_item.fullname").alias("fullname"),
            F.coalesce(_col(filtered, "_item.spk"), _col(filtered, "_item.spkid")).alias("spk"),
            _col(filtered, "_item.ip", DOUBLE).alias("ip"),
            _col(filtered, "_item.date").alias("date"),
            _col(filtered, "_item.dist", DOUBLE).alias("dist"),
            _col(filtered, "_item.width", DOUBLE).alias("width"),
            F.coalesce(
                _col(filtered, "_item.sigma_imp", DOUBLE),
                _col(filtered, "_item.sigma_vi", DOUBLE),
            ).alias("sigma_imp"),
            _col(filtered, "_item.ps", DOUBLE).alias("ps"),
            _col(filtered, "_item.ts", DOUBLE).alias("ts"),
            _col(filtered, "_item.energy", DOUBLE).alias("energy"),
            F.coalesce(
                _col(filtered, "_item.vinf", DOUBLE),
                _col(filtered, "_item.v_inf", DOUBLE),
            ).alias("vinf"),
            F.to_json(F.col("_item")).alias("raw_json"),
        )
        return _cast_to_schema(selected, SENTRY_VI_COLUMNS)

    def transform_ingestion_events(self, bronze_df: DataFrame) -> DataFrame:
        selected = bronze_df.select(
            _source_col(bronze_df).alias("source"),
            _col(bronze_df, "metadata.ingested_at_utc").alias("ingested_at_utc"),
            _col(bronze_df, "ingest_date").alias("ingest_date"),
            _col(bronze_df, "metadata.object_id").alias("object_id"),
            F.coalesce(_json_col(bronze_df, "metadata.query_params"), F.lit("{}")).alias(
                "query_params_json"
            ),
            _col(bronze_df, "metadata.api_signature.version").alias("api_signature_version"),
            _col(bronze_df, "bronze_file_path").alias("bronze_file_path"),
        )
        return _cast_to_schema(selected, INGESTION_EVENT_COLUMNS)


def _empty_df(spark: SparkSession, columns: list[tuple[str, T.DataType]]) -> DataFrame:
    return spark.createDataFrame(
        [], T.StructType([T.StructField(name, dtype, True) for name, dtype in columns])
    )


def _cast_to_schema(df: DataFrame, columns: list[tuple[str, T.DataType]]) -> DataFrame:
    return df.select(*(F.col(name).cast(dtype).alias(name) for name, dtype in columns))


def _has_field(df: DataFrame, path: str) -> bool:
    return _field_type(df, path) is not None


def _field_type(df: DataFrame, path: str) -> T.DataType | None:
    data_type: T.DataType = df.schema
    for part in path.split("."):
        if isinstance(data_type, T.StructType):
            field = next((field for field in data_type.fields if field.name == part), None)
            if field is None:
                return None
            data_type = field.dataType
        elif isinstance(data_type, T.ArrayType) and isinstance(data_type.elementType, T.StructType):
            field = next(
                (field for field in data_type.elementType.fields if field.name == part), None
            )
            if field is None:
                return None
            data_type = field.dataType
        else:
            return None
    return data_type


def _col(df: DataFrame, path: str, data_type: T.DataType = STRING) -> Column:
    source_type = _field_type(df, path)
    if source_type is None or isinstance(source_type, (T.StructType, T.ArrayType, T.MapType)):
        return F.lit(None).cast(data_type)
    return F.col(path).cast(data_type)


def _json_col(df: DataFrame, path: str) -> Column:
    if not _has_field(df, path):
        return F.lit(None).cast(STRING)
    return F.to_json(F.col(path)).cast(STRING)


def _source_col(df: DataFrame) -> Column:
    return F.coalesce(_col(df, "metadata.source"), F.lit("unknown"))


def _flag_to_bool(value: Column) -> Column:
    normalized = F.lower(F.trim(value.cast(STRING)))
    return (
        F.when(normalized.isin("true", "t", "1", "yes", "y"), F.lit(True))
        .when(normalized.isin("false", "f", "0", "no", "n"), F.lit(False))
        .otherwise(F.lit(None).cast(BOOLEAN))
    )


def _array_value_by_name(
    df: DataFrame,
    array_path: str,
    name: str,
    data_type: T.DataType = STRING,
) -> Column:
    if not (_has_field(df, array_path) and _has_field(df, f"{array_path}.name")):
        return F.lit(None).cast(data_type)
    expression = (
        f"try_element_at(transform(filter({array_path}, "
        f"x -> lower(x.name) = '{name.lower()}'), x -> x.value), 1)"
    )
    return F.expr(expression).cast(data_type)


def _orbital_element(df: DataFrame, name: str) -> Column:
    return F.coalesce(
        _array_value_by_name(df, "data.orbit.elements", name, DOUBLE),
        _col(df, f"data.orbit_defs.{name}", DOUBLE),
    )
