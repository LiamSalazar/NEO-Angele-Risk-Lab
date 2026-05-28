from __future__ import annotations

from neo_ange.etl.bronze_reader import BronzeReader
from neo_ange.etl.silver_transformers import SilverTransformers


def test_transform_sbdb_object_extracts_orbital_elements(spark, tmp_path, write_bronze) -> None:
    write_bronze(
        "sbdb_object",
        {
            "signature": {"version": "1.3"},
            "object": {
                "spkid": "2000433",
                "fullname": "433 Eros",
                "des": "433",
                "shortname": "Eros",
                "neo": "Y",
                "pha": "N",
                "kind": "an",
                "orbit_class": {"code": "AMO", "name": "Amor"},
            },
            "orbit": {
                "orbit_id": "JPL 1",
                "condition_code": "0",
                "soln_date": "2026-01-01",
                "data_arc": "1000",
                "n_obs_used": "42",
                "rms": "0.12",
                "moid": "0.15",
                "elements": [
                    {"name": "e", "value": "0.22"},
                    {"name": "a", "value": "1.45"},
                    {"name": "q", "value": "1.13"},
                    {"name": "i", "value": "10.8"},
                ],
            },
            "phys_par": [
                {"name": "H", "value": "10.4"},
                {"name": "diameter", "value": "16.8"},
                {"name": "albedo", "value": "0.25"},
            ],
        },
        object_id="433",
    )
    bronze_df = BronzeReader(spark, tmp_path / "bronze").read_sbdb_object()

    silver_df = SilverTransformers(spark).transform_sbdb_objects(bronze_df)
    row = silver_df.first().asDict()

    assert row["spkid"] == "2000433"
    assert row["neo"] is True
    assert row["pha"] is False
    assert row["orbit_class_code"] == "AMO"
    assert row["h"] == 10.4
    assert row["diameter"] == 16.8
    assert row["e"] == 0.22
    assert row["a"] == 1.45
    assert row["raw_json"]


def test_transform_close_approaches_uses_fields_and_data(spark, tmp_path, write_bronze) -> None:
    write_bronze(
        "cad",
        {
            "signature": {"version": "1.5"},
            "fields": [
                "des",
                "orbit_id",
                "jd",
                "cd",
                "dist",
                "dist_min",
                "dist_max",
                "v_rel",
                "v_inf",
                "t_sigma_f",
                "h",
                "diameter",
                "diameter_sigma",
                "fullname",
            ],
            "data": [
                [
                    "2026 BC",
                    "2",
                    "2461041.5",
                    "2026-Jan-01 01:43",
                    "0.05",
                    "0.04",
                    "0.06",
                    "11.0",
                    "10.9",
                    "00:52",
                    "26.3",
                    "0.01",
                    "0.001",
                    "(2026 BC)",
                ]
            ],
        },
        query_params={"body": "Earth"},
    )
    bronze_df = BronzeReader(spark, tmp_path / "bronze").read_cad()

    silver_df = SilverTransformers(spark).transform_close_approaches(bronze_df)
    row = silver_df.first().asDict()

    assert row["des"] == "2026 BC"
    assert row["dist"] == 0.05
    assert row["v_rel"] == 11.0
    assert row["body"] == "Earth"
    assert row["close_approach_datetime"] == "2026-Jan-01 01:43"


def test_transform_sentry_summary_and_virtual_impactors(spark, tmp_path, write_bronze) -> None:
    write_bronze(
        "sentry",
        {
            "signature": {"version": "2.0"},
            "data": [
                {
                    "des": "2026 AB",
                    "fullname": "(2026 AB)",
                    "spk": "123",
                    "h": "22.1",
                    "diameter": "0.12",
                    "ip": "1e-6",
                    "ps_cum": "-3.2",
                    "ps_max": "-3.5",
                    "ts_max": "0",
                    "last_obs": "2026-01-02",
                    "n_imp": 2,
                    "last_obs_jd": "2461000.5",
                }
            ],
        },
        object_id="summary",
    )
    write_bronze(
        "sentry",
        {
            "signature": {"version": "2.0"},
            "data": [
                {
                    "des": "2026 AB",
                    "fullname": "(2026 AB)",
                    "spk": "123",
                    "ip": "1e-7",
                    "date": "2080-01-01",
                    "dist": "0.001",
                    "width": "0.2",
                    "sigma_vi": "1.5",
                    "ps": "-5.1",
                    "ts": "0",
                    "energy": "0.3",
                    "vinf": "12.4",
                }
            ],
        },
        query_params={"all": 1},
        object_id="virtual_impactors",
    )
    bronze_df = BronzeReader(spark, tmp_path / "bronze").read_sentry()
    transformers = SilverTransformers(spark)

    sentry_df = transformers.transform_sentry_objects(bronze_df)
    vi_df = transformers.transform_sentry_virtual_impactors(bronze_df)

    assert sentry_df.count() == 1
    assert vi_df.count() == 1
    assert sentry_df.first()["ip"] == 1e-6
    assert vi_df.first()["sigma_imp"] == 1.5
