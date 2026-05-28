from __future__ import annotations

from pyspark.sql import types as T

from neo_ange.etl.gold_builder import GoldBuilder
from neo_ange.etl.silver_transformers import CAD_COLUMNS, SBDB_OBJECT_COLUMNS, SENTRY_OBJECT_COLUMNS
from neo_ange.etl.writers import ParquetTableWriter


def schema(columns):
    return T.StructType([T.StructField(name, dtype, True) for name, dtype in columns])


def test_gold_builder_generates_initial_feature_dataset(spark, tmp_path) -> None:
    silver_root = tmp_path / "silver"
    gold_root = tmp_path / "gold"
    writer = ParquetTableWriter()
    writer.write(
        spark.createDataFrame(
            [
                {
                    "object_id": "433",
                    "source": "sbdb_object",
                    "ingested_at_utc": "2026-05-28T00:00:00Z",
                    "spkid": "2000433",
                    "full_name": "433 Eros",
                    "pdes": "2026 AB",
                    "name": "Eros",
                    "neo": True,
                    "pha": False,
                    "orbit_class_code": "AMO",
                    "orbit_class_name": "Amor",
                    "h": 10.4,
                    "diameter": 16.8,
                    "albedo": 0.25,
                    "e": 0.22,
                    "a": 1.45,
                    "q": 1.13,
                    "i": 10.8,
                    "moid": 0.15,
                    "moid_ld": 58.3,
                    "condition_code": "0",
                    "arc_length": 1000.0,
                    "n_obs_used": 42,
                    "rms": 0.12,
                }
            ],
            schema=schema(SBDB_OBJECT_COLUMNS),
        ),
        silver_root / "sbdb_objects",
    )
    writer.write(
        spark.createDataFrame(
            [
                {
                    "source": "cad",
                    "ingested_at_utc": "2026-05-28T00:00:00Z",
                    "des": "2026 AB",
                    "jd": 2461041.5,
                    "close_approach_datetime": "2026-Jan-01 01:43",
                    "dist": 0.05,
                    "dist_min": 0.04,
                    "dist_max": 0.06,
                    "v_rel": 11.0,
                }
            ],
            schema=schema(CAD_COLUMNS),
        ),
        silver_root / "close_approaches",
    )
    writer.write(
        spark.createDataFrame(
            [
                {
                    "source": "sentry",
                    "ingested_at_utc": "2026-05-28T00:00:00Z",
                    "des": "2026 AB",
                    "spk": "2000433",
                    "fullname": "(2026 AB)",
                    "ip": 1e-6,
                    "ps_cum": -3.2,
                    "ps_max": -3.5,
                    "ts_max": 0.0,
                    "n_imp": 2,
                }
            ],
            schema=schema(SENTRY_OBJECT_COLUMNS),
        ),
        silver_root / "sentry_objects",
    )

    gold_df = GoldBuilder(spark, silver_root, gold_root).build_neo_risk_features()
    row = gold_df.first().asDict()

    assert row["object_key"] == "2000433"
    assert row["des"] == "2026 AB"
    assert row["sentry_flag"] is True
    assert row["min_close_approach_dist"] == 0.05
    assert 0 <= row["feature_completeness_ratio"] <= 1
    assert 0 <= row["inverse_moid"] <= 1
    assert "relative_velocity_score" in gold_df.columns


def test_gold_builder_supports_absent_cad_and_sentry(spark, tmp_path) -> None:
    silver_root = tmp_path / "silver"
    ParquetTableWriter().write(
        spark.createDataFrame(
            [
                {
                    "object_id": "1",
                    "source": "sbdb_object",
                    "ingested_at_utc": "2026-05-28T00:00:00Z",
                    "spkid": "1",
                    "full_name": "Object 1",
                    "pdes": "2026 AA",
                    "neo": True,
                    "pha": None,
                    "moid": 0.0,
                }
            ],
            schema=schema(SBDB_OBJECT_COLUMNS),
        ),
        silver_root / "sbdb_objects",
    )

    gold_df = GoldBuilder(spark, silver_root, tmp_path / "gold").build_neo_risk_features()
    row = gold_df.first().asDict()

    assert row["object_key"] == "1"
    assert row["sentry_flag"] is False
    assert row["inverse_moid"] == 1.0
    assert row["min_close_approach_dist"] is None
