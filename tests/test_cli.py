from __future__ import annotations

from typer.testing import CliRunner

from neo_ange import cli

runner = CliRunner()


def test_info_command_works() -> None:
    result = runner.invoke(cli.app, ["info"])

    assert result.exit_code == 0
    assert "Neo Angele Risk Lab" in result.output
    assert "Package version" in result.output


def test_ingest_sample_command_works_with_pipeline_mock(monkeypatch, tmp_path) -> None:
    class FakePipeline:
        def ingest_sample_bundle(self):
            output = tmp_path / "sample.json"
            output.write_text("{}", encoding="utf-8")
            return [output]

    monkeypatch.setattr(cli, "build_pipeline", lambda: FakePipeline())

    result = runner.invoke(cli.app, ["ingest", "sample"])

    assert result.exit_code == 0
    assert "sample.json" in result.output
