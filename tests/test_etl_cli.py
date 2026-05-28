from __future__ import annotations

from typer.testing import CliRunner

from neo_ange import cli
from neo_ange.pipelines.etl import ETLPipeline

runner = CliRunner()


def test_etl_status_command_works() -> None:
    result = runner.invoke(cli.app, ["etl", "status"])

    assert result.exit_code == 0
    assert "Spark ETL status" in result.output
    assert "Bronze sources available" in result.output


def test_etl_commands_are_registered() -> None:
    result = runner.invoke(cli.app, ["etl", "--help"])

    assert result.exit_code == 0
    assert "bronze-to-silver" in result.output
    assert "build-gold" in result.output
    assert "run-all" in result.output


def test_etl_pipeline_runs_with_synthetic_bronze(spark, tmp_path, write_bronze) -> None:
    write_bronze(
        "sbdb_object",
        {
            "signature": {"version": "1.3"},
            "object": {"spkid": "1", "des": "2026 AA", "fullname": "Object 1", "neo": "Y"},
            "orbit": {
                "moid": "0.1",
                "elements": [{"name": "e", "value": "0.2"}],
                "n_obs_used": "5",
            },
            "phys_par": [{"name": "H", "value": "20.0"}],
        },
        object_id="2026 AA",
    )
    pipeline = ETLPipeline(
        spark=spark,
        bronze_root=tmp_path / "bronze",
        silver_root=tmp_path / "silver",
        gold_root=tmp_path / "gold",
    )

    result = pipeline.run_all()

    assert result["status"] in {"success", "partial_success"}
    assert (tmp_path / "silver" / "sbdb_objects").exists()
    assert (tmp_path / "gold" / "neo_risk_features").exists()
    assert (tmp_path / "gold" / "quality_reports").exists()
