from __future__ import annotations

import pytest

from neo_ange.etl.bronze_reader import BronzeReader, BronzeSourceNotFoundError


def test_bronze_reader_detects_and_reads_available_sources(spark, tmp_path, write_bronze) -> None:
    write_bronze("sbdb_object", {"signature": {"version": "1"}, "object": {"spkid": "1"}})

    reader = BronzeReader(spark, tmp_path / "bronze")

    assert reader.source_exists("sbdb_object")
    assert reader.list_available_sources() == ["sbdb_object"]

    df = reader.read_source("sbdb_object")
    row = df.select(
        "metadata.source",
        "metadata.ingested_at_utc",
        "metadata.query_params",
        "metadata.api_signature",
        "data.object.spkid",
        "ingest_date",
        "bronze_file_path",
    ).first()

    assert row["source"] == "sbdb_object"
    assert row["spkid"] == "1"
    assert row["ingest_date"] == "2026-05-28"
    assert "sbdb_object" in row["bronze_file_path"]


def test_bronze_reader_missing_source_raises_clear_error(spark, tmp_path) -> None:
    reader = BronzeReader(spark, tmp_path / "bronze")

    with pytest.raises(BronzeSourceNotFoundError, match="not available"):
        reader.read_source("cad")
