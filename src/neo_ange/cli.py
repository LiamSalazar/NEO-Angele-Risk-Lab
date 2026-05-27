"""Command-line interface for Neo Angele Risk Lab."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from neo_ange import __version__
from neo_ange.clients.base import JPLClientError
from neo_ange.pipelines.ingestion import IngestionPipeline
from neo_ange.utils.config import get_settings, load_yaml_file
from neo_ange.utils.logging import setup_logging

PROJECT_NAME = "Neo Angele Risk Lab"

console = Console()
app = typer.Typer(help="Neo Angele Risk Lab command-line interface.")
ingest_app = typer.Typer(help="Ingest public NASA/JPL API data into bronze storage.")
app.add_typer(ingest_app, name="ingest")


def build_pipeline() -> IngestionPipeline:
    return IngestionPipeline()


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


if __name__ == "__main__":
    app()
