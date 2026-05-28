from __future__ import annotations

from typer.testing import CliRunner

from neo_ange import cli

runner = CliRunner()


def test_ml_feature_sets_command_works() -> None:
    result = runner.invoke(cli.app, ["ml", "feature-sets"])

    assert result.exit_code == 0
    assert "full_features" in result.output
    assert "no_definition_features" in result.output


def test_ml_status_command_works_without_gold() -> None:
    result = runner.invoke(cli.app, ["ml", "status"])

    assert result.exit_code == 0
    assert "Baseline ML status" in result.output
    assert "Gold dataset" in result.output


def test_expand_discover_curated_command_works() -> None:
    result = runner.invoke(
        cli.app,
        ["expand", "discover", "--strategy", "curated", "--limit", "3"],
    )

    assert result.exit_code == 0
    assert "99942" in result.output
    assert "433" in result.output


def test_new_command_groups_are_registered() -> None:
    result = runner.invoke(cli.app, ["ml", "--help"])
    expand_result = runner.invoke(cli.app, ["expand", "--help"])

    assert result.exit_code == 0
    assert "train-baselines" in result.output
    assert "leakage-audit" in result.output
    assert expand_result.exit_code == 0
    assert "ingest-objects" in expand_result.output
