"""Command-line interface for Neo Angele Risk Lab."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from neo_ange import __version__
from neo_ange.clients.base import JPLClientError
from neo_ange.pipelines.etl import ETLPipeline
from neo_ange.pipelines.ingestion import IngestionPipeline
from neo_ange.services.gold_storage import GoldStorage
from neo_ange.services.silver_storage import SilverStorage
from neo_ange.spark.session import create_spark_session, stop_spark_session
from neo_ange.utils.config import get_settings, load_yaml_file
from neo_ange.utils.logging import setup_logging

PROJECT_NAME = "Neo Angele Risk Lab"

console = Console()
app = typer.Typer(help="Neo Angele Risk Lab command-line interface.")
ingest_app = typer.Typer(help="Ingest public NASA/JPL API data into bronze storage.")
etl_app = typer.Typer(help="Run Spark ETL from bronze to silver and gold features.")
app.add_typer(ingest_app, name="ingest")
app.add_typer(etl_app, name="etl")


def build_pipeline() -> IngestionPipeline:
    return IngestionPipeline()


def build_etl_pipeline(spark) -> ETLPipeline:
    settings = get_settings()
    return ETLPipeline(
        spark=spark,
        bronze_root=Path(settings.data_dir) / "bronze",
        silver_root=settings.silver_dir,
        gold_root=settings.gold_dir,
    )


def _print_saved_paths(paths: list[Path]) -> None:
    if not paths:
        console.print("[yellow]No files were saved.[/yellow]")
        return
    table = Table(title="Saved bronze files")
    table.add_column("Path", overflow="fold")
    for path in paths:
        table.add_row(str(path))
    console.print(table)


def _run_ingestion(operation: str, callback: typer.CallbackParam) -> None:
    settings = get_settings()
    setup_logging(settings.log_level)
    try:
        result = callback()
    except JPLClientError as exc:
        console.print(f"[red]{operation} failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        console.print(f"[red]{operation} failed unexpectedly:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    paths = result if isinstance(result, list) else [result]
    _print_saved_paths(paths)


def _run_etl(operation: str, callback: typer.CallbackParam) -> None:
    settings = get_settings()
    setup_logging(settings.log_level)
    spark = None
    try:
        spark = create_spark_session(
            app_name=settings.spark_app_name,
            master=settings.spark_master,
            log_level=settings.spark_log_level,
        )
        result = callback(build_etl_pipeline(spark))
    except Exception as exc:
        console.print(f"[red]{operation} failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    finally:
        if spark is not None:
            stop_spark_session(spark)

    console.print(json.dumps(result, indent=2, sort_keys=True))
    if result.get("status") == "failed":
        raise typer.Exit(code=1)


@app.command()
def info() -> None:
    """Show project and runtime configuration."""
    settings = get_settings()
    datasources = load_yaml_file("configs/datasources.yaml").get("datasources", {})

    table = Table(title=PROJECT_NAME)
    table.add_column("Setting")
    table.add_column("Value", overflow="fold")
    table.add_row("Project", PROJECT_NAME)
    table.add_row("Package version", __version__)
    table.add_row("Environment", settings.env)
    table.add_row("Data directory", str(settings.data_dir))
    table.add_row("Request timeout", f"{settings.request_timeout}s")

    console.print(Panel.fit("Public NASA/JPL ingestion foundation", title=PROJECT_NAME))
    console.print(table)

    endpoint_table = Table(title="Configured endpoints")
    endpoint_table.add_column("Source")
    endpoint_table.add_column("Base URL", overflow="fold")
    for key, value in datasources.items():
        endpoint_table.add_row(key, str(value.get("base_url", "")))
    console.print(endpoint_table)


@etl_app.command("bronze-to-silver")
def etl_bronze_to_silver(
    source: str | None = typer.Option(
        None,
        "--source",
        help="Optional source to process: sbdb_object, cad, sentry, or sbdb_query.",
    ),
) -> None:
    """Transform bronze JSON wrappers into silver Parquet tables."""

    def callback(pipeline: ETLPipeline) -> dict:
        return pipeline.run_bronze_to_silver(source=source)

    _run_etl("Bronze-to-silver ETL", callback)


@etl_app.command("build-gold")
def etl_build_gold() -> None:
    """Build the gold neo_risk_features dataset and quality report."""

    def callback(pipeline: ETLPipeline) -> dict:
        return pipeline.run_gold()

    _run_etl("Gold feature build", callback)


@etl_app.command("run-all")
def etl_run_all() -> None:
    """Run bronze-to-silver ETL, gold feature build, and quality checks."""

    def callback(pipeline: ETLPipeline) -> dict:
        return pipeline.run_all()

    _run_etl("Full ETL", callback)


@etl_app.command("status")
def etl_status() -> None:
    """Show bronze, silver, gold, and quality-report availability."""
    settings = get_settings()
    bronze_root = Path(settings.data_dir) / "bronze"
    silver_storage = SilverStorage(settings.silver_dir)
    gold_storage = GoldStorage(settings.gold_dir)

    console.print(Panel.fit("Spark ETL status", title=PROJECT_NAME))

    paths_table = Table(title="Data root paths")
    paths_table.add_column("Layer")
    paths_table.add_column("Path", overflow="fold")
    paths_table.add_row("bronze", str(bronze_root))
    paths_table.add_row("silver", str(settings.silver_dir))
    paths_table.add_row("gold", str(settings.gold_dir))
    console.print(paths_table)

    bronze_sources = _list_bronze_sources(bronze_root)
    silver_tables = silver_storage.list_tables()
    gold_tables = gold_storage.list_tables()
    quality_reports = gold_storage.latest_quality_reports()

    _print_list_table("Bronze sources available", bronze_sources)
    _print_list_table("Silver tables available", silver_tables)
    _print_list_table("Gold tables available", gold_tables)
    _print_list_table("Latest quality reports", [str(path) for path in quality_reports])


@ingest_app.command("sbdb-query")
def ingest_sbdb_query(limit: int = typer.Option(100, "--limit", min=1)) -> None:
    """Ingest a NEO sample from the SBDB Query API."""

    def callback() -> Path:
        return build_pipeline().ingest_sbdb_query_sample(limit=limit)

    _run_ingestion("SBDB Query ingestion", callback)


@ingest_app.command("object")
def ingest_object(
    designation: str = typer.Option(..., "--designation", "-d"),
    rich: bool = typer.Option(True, "--rich/--basic"),
) -> None:
    """Ingest one SBDB object by designation or search string."""

    def callback() -> Path:
        return build_pipeline().ingest_object(designation, rich=rich)

    _run_ingestion("SBDB Object ingestion", callback)


@ingest_app.command("cad")
def ingest_cad(
    date_min: str = typer.Option("now", "--date-min"),
    date_max: str = typer.Option("+60", "--date-max"),
    dist_max: str = typer.Option("0.05", "--dist-max"),
    limit: int = typer.Option(100, "--limit", min=1),
) -> None:
    """Ingest close approach records from CAD."""

    def callback() -> Path:
        return build_pipeline().ingest_cad_sample(
            date_min=date_min,
            date_max=date_max,
            dist_max=dist_max,
            limit=limit,
        )

    _run_ingestion("CAD ingestion", callback)


@ingest_app.command("sentry")
def ingest_sentry() -> None:
    """Ingest Sentry summary data."""

    def callback() -> Path:
        return build_pipeline().ingest_sentry_summary()

    _run_ingestion("Sentry summary ingestion", callback)


@ingest_app.command("sentry-vi")
def ingest_sentry_vi(ip_min: float | None = typer.Option(None, "--ip-min")) -> None:
    """Ingest Sentry virtual impactor data."""

    def callback() -> Path:
        return build_pipeline().ingest_sentry_virtual_impactors(ip_min=ip_min)

    _run_ingestion("Sentry virtual impactor ingestion", callback)


@ingest_app.command("sample")
def ingest_sample() -> None:
    """Run the multi-source sample ingestion bundle."""

    def callback() -> list[Path]:
        pipeline = build_pipeline()
        paths = pipeline.ingest_sample_bundle()
        failures = getattr(pipeline, "last_failures", [])
        if failures:
            table = Table(title="Bundle failures")
            table.add_column("Task")
            table.add_column("Error", overflow="fold")
            for task, error in failures:
                table.add_row(task, error)
            console.print(table)
        return paths

    _run_ingestion("Sample bundle ingestion", callback)


def _list_bronze_sources(bronze_root: Path) -> list[str]:
    if not bronze_root.exists():
        return []
    return sorted(
        child.name
        for child in bronze_root.iterdir()
        if child.is_dir() and any(child.rglob("*.json"))
    )


def _print_list_table(title: str, values: list[str]) -> None:
    console.print(f"[bold]{title}[/bold]")
    table = Table()
    table.add_column("Name", overflow="fold")
    if values:
        for value in values:
            table.add_row(value)
    else:
        table.add_row("[yellow]None found[/yellow]")
    console.print(table)


if __name__ == "__main__":
    app()
