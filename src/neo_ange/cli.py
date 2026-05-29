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
from neo_ange.expansion.discovery import ObjectDiscoveryService
from neo_ange.manifests.run_manifest import list_manifests, load_latest_manifest
from neo_ange.ml.dataset import MLDatasetLoader
from neo_ange.ml.feature_sets import FeatureSetRegistry
from neo_ange.pipelines.etl import ETLPipeline
from neo_ange.pipelines.ingestion import IngestionPipeline
from neo_ange.pipelines.ml import MLPipeline
from neo_ange.pipelines.risk import RiskPipeline
from neo_ange.pipelines.simulation import SimulationPipeline
from neo_ange.risk.categories import RiskCategoryAssigner
from neo_ange.services.gold_storage import GoldStorage
from neo_ange.services.silver_storage import SilverStorage
from neo_ange.spark.session import create_spark_session, stop_spark_session
from neo_ange.utils.config import get_settings, load_yaml_file
from neo_ange.utils.logging import setup_logging
from neo_ange.utils.serialization import to_jsonable

PROJECT_NAME = "Neo Angele Risk Lab"

console = Console()
app = typer.Typer(help="Neo Angele Risk Lab command-line interface.")
ingest_app = typer.Typer(help="Ingest public NASA/JPL API data into bronze storage.")
etl_app = typer.Typer(help="Run Spark ETL from bronze to silver and gold features.")
expand_app = typer.Typer(help="Discover and ingest additional SBDB Object payloads.")
ml_app = typer.Typer(help="Run baseline ML experiments and leakage audits.")
risk_app = typer.Typer(help="Build and inspect experimental risk-priority scores.")
api_app = typer.Typer(help="Inspect or run the FastAPI backend.")
simulate_app = typer.Typer(help="Run approximate Monte Carlo score simulations.")
app.add_typer(ingest_app, name="ingest")
app.add_typer(etl_app, name="etl")
app.add_typer(expand_app, name="expand")
app.add_typer(ml_app, name="ml")
app.add_typer(risk_app, name="risk")
app.add_typer(api_app, name="api")
app.add_typer(simulate_app, name="simulate")


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


def build_discovery_service() -> ObjectDiscoveryService:
    settings = get_settings()
    return ObjectDiscoveryService(
        silver_root=settings.silver_dir,
        bronze_root=Path(settings.data_dir) / "bronze",
    )


def build_ml_pipeline() -> MLPipeline:
    settings = get_settings()
    return MLPipeline(gold_root=settings.gold_dir)


def build_risk_pipeline() -> RiskPipeline:
    settings = get_settings()
    return RiskPipeline(gold_root=settings.gold_dir)


def build_simulation_pipeline() -> SimulationPipeline:
    settings = get_settings()
    return SimulationPipeline(gold_root=settings.gold_dir)


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


def _run_ml(operation: str, callback: typer.CallbackParam) -> None:
    settings = get_settings()
    setup_logging(settings.log_level)
    try:
        result = callback()
    except Exception as exc:
        console.print(f"[red]{operation} failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

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

    console.print(
        Panel.fit(
            "NASA/JPL ingestion, Spark ETL, feature engineering, and baseline ML",
            title=PROJECT_NAME,
        )
    )
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


@expand_app.command("discover")
def expand_discover(
    strategy: str = typer.Option("all", "--strategy"),
    limit: int = typer.Option(100, "--limit", min=1),
) -> None:
    """Discover local SBDB designations without calling the internet."""
    discovery = build_discovery_service()
    designations = _discover_designations(discovery, strategy=strategy, limit=limit)

    table = Table(title=f"Discovered designations ({len(designations)})")
    table.add_column("Designation", overflow="fold")
    for designation in designations:
        table.add_row(designation)
    console.print(table)
    if discovery.warnings:
        _print_list_table("Discovery warnings", discovery.warnings)


@expand_app.command("ingest-objects")
def expand_ingest_objects(
    strategy: str = typer.Option("all", "--strategy"),
    limit: int = typer.Option(100, "--limit", min=1),
    rich: bool = typer.Option(True, "--rich/--basic"),
    skip_existing: bool = typer.Option(True, "--skip-existing/--no-skip-existing"),
) -> None:
    """Discover designations and ingest SBDB Object payloads into bronze."""
    settings = get_settings()
    setup_logging(settings.log_level)
    try:
        result = build_pipeline().ingest_discovered_objects(
            strategy=strategy,
            limit=limit,
            rich=rich,
            skip_existing=skip_existing,
        )
    except JPLClientError as exc:
        console.print(f"[red]Bulk SBDB Object ingestion failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        console.print(f"[red]Bulk SBDB Object ingestion failed unexpectedly:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(json.dumps(result, indent=2, sort_keys=True))
    if result.get("status") == "failed":
        raise typer.Exit(code=1)


@ml_app.command("status")
def ml_status() -> None:
    """Show gold dataset and latest ML artifact status."""
    settings = get_settings()
    loader = MLDatasetLoader(settings.gold_dir)
    df = loader.load_gold_features()
    validation = loader.validate_target(df, target="pha")
    reports_dir = Path("reports/ml")

    console.print(Panel.fit("Baseline ML status", title=PROJECT_NAME))
    table = Table(title="Gold dataset")
    table.add_column("Item")
    table.add_column("Value", overflow="fold")
    table.add_row("Path", str(loader.features_path))
    table.add_row("Rows", str(len(df)))
    table.add_row("Columns", str(len(df.columns)))
    table.add_row("Target status", validation["status"])
    table.add_row("PHA positives", str(validation["n_positive"]))
    table.add_row("PHA negatives", str(validation["n_negative"]))
    table.add_row("PHA positive rate", str(validation["positive_rate"]))
    console.print(table)

    latest_reports = _latest_paths(reports_dir, patterns=["*.json", "*.csv", "*.md"])
    _print_list_table("Latest ML reports", [str(path) for path in latest_reports])
    latest_ml_manifest = load_latest_manifest("ml")
    latest_manifests = list_manifests("ml")[-5:]
    _print_list_table("Latest ML manifests", [str(path) for path in latest_manifests])
    if latest_ml_manifest:
        console.print(f"[bold]Latest ML manifest status:[/bold] {latest_ml_manifest.get('status')}")


@ml_app.command("train-baselines")
def ml_train_baselines(
    target: str = typer.Option("pha", "--target"),
    min_rows: int = typer.Option(100, "--min-rows", min=1),
    min_positive: int = typer.Option(5, "--min-positive", min=1),
) -> None:
    """Run baseline ML experiments when the gold dataset is large enough."""

    def callback() -> dict:
        return build_ml_pipeline().run_baselines(
            target=target,
            min_rows=min_rows,
            min_positive=min_positive,
        )

    _run_ml("Baseline ML training", callback)


@ml_app.command("leakage-audit")
def ml_leakage_audit(target: str = typer.Option("pha", "--target")) -> None:
    """Generate leakage audit reports from the latest baseline results."""

    def callback() -> dict:
        return build_ml_pipeline().run_leakage_audit(target=target)

    _run_ml("PHA leakage audit", callback)


@ml_app.command("run-all")
def ml_run_all(
    target: str = typer.Option("pha", "--target"),
    min_rows: int = typer.Option(100, "--min-rows", min=1),
    min_positive: int = typer.Option(5, "--min-positive", min=1),
) -> None:
    """Run baseline ML and leakage audit reports."""

    def callback() -> dict:
        pipeline = build_ml_pipeline()
        baseline_result = pipeline.run_baselines(
            target=target,
            min_rows=min_rows,
            min_positive=min_positive,
        )
        leakage_result = pipeline.run_leakage_audit(target=target)
        return {
            "status": baseline_result["status"],
            "target": target,
            "outputs": {
                **baseline_result.get("outputs", {}),
                **leakage_result.get("outputs", {}),
            },
            "metrics_summary": baseline_result.get("metrics_summary", {}),
            "warnings": [
                *baseline_result.get("warnings", []),
                *leakage_result.get("warnings", []),
            ],
            "errors": [
                *baseline_result.get("errors", []),
                *leakage_result.get("errors", []),
            ],
        }

    _run_ml("Full ML pipeline", callback)


@ml_app.command("feature-sets")
def ml_feature_sets() -> None:
    """List registered ML feature sets."""
    registry = FeatureSetRegistry()
    table = Table(title="ML feature sets")
    table.add_column("Name")
    table.add_column("Feature count", justify="right")
    table.add_column("Description", overflow="fold")
    for definition in registry.list_feature_sets():
        table.add_row(
            definition.name,
            str(len(definition.features)),
            definition.description,
        )
    console.print(table)


@risk_app.command("status")
def risk_status() -> None:
    """Show experimental risk-score availability."""
    status_payload = build_risk_pipeline().status()
    console.print(Panel.fit("Risk score status", title=PROJECT_NAME))
    _print_key_value_table("Risk pipeline", status_payload)
    if not status_payload["gold_features_available"]:
        console.print(
            "[yellow]Gold features not found. Run: python -m neo_ange.cli etl run-all[/yellow]"
        )
    if not status_payload["risk_scores_available"]:
        console.print(
            "[yellow]Risk scores not found. Run: python -m neo_ange.cli risk build[/yellow]"
        )


@risk_app.command("build")
def risk_build() -> None:
    """Build experimental risk-priority scores and reports."""
    result = build_risk_pipeline().build_scores()
    console.print(json.dumps(to_jsonable(result), indent=2, sort_keys=True))
    if result.get("status") == "failed":
        raise typer.Exit(code=1)


@risk_app.command("top")
def risk_top(limit: int = typer.Option(20, "--limit", min=1)) -> None:
    """Show top objects by experimental risk-priority score."""
    pipeline = build_risk_pipeline()
    rows = pipeline.top(limit=limit)
    if not rows:
        console.print(
            "[yellow]Risk scores not found. Run: python -m neo_ange.cli risk build[/yellow]"
        )
        return
    table = Table(title=f"Top {len(rows)} risk-priority objects")
    for column in ["object_key", "des", "risk_score_0_100", "risk_category"]:
        table.add_column(column, overflow="fold")
    for row in rows:
        table.add_row(
            str(row.get("object_key", "")),
            str(row.get("des", "")),
            f"{float(row.get('risk_score_0_100') or 0):.2f}",
            str(row.get("risk_category", "")),
        )
    console.print(table)


@risk_app.command("explain")
def risk_explain(object_key: str = typer.Option(..., "--object-key")) -> None:
    """Explain one object's experimental risk-priority score."""
    explanation = build_risk_pipeline().explain(object_key)
    console.print(json.dumps(to_jsonable(explanation), indent=2, sort_keys=True))
    if explanation.get("status") in {"missing_data", "not_found"}:
        raise typer.Exit(code=1)


@risk_app.command("categories")
def risk_categories() -> None:
    """List configured risk-priority categories."""
    categories = RiskCategoryAssigner().all_categories()
    table = Table(title="Risk-priority categories")
    table.add_column("Category")
    table.add_column("Range")
    table.add_column("Description", overflow="fold")
    for name, metadata in categories.items():
        table.add_row(
            name,
            f"{metadata['min']} <= score < {metadata['max']}",
            str(metadata["description"]),
        )
    console.print(table)


@api_app.command("info")
def api_info() -> None:
    """Show FastAPI import path and route groups."""
    table = Table(title="FastAPI backend")
    table.add_column("Item")
    table.add_column("Value", overflow="fold")
    table.add_row("App import path", "neo_ange.api.main:app")
    table.add_row("Run command", "uvicorn neo_ange.api.main:app --reload")
    table.add_row("Route groups", "health, objects, rankings, risk, simulations")
    table.add_row("Local docs", "http://127.0.0.1:8000/docs")
    console.print(table)


@api_app.command("run")
def api_run(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8000, "--port", min=1, max=65535),
    reload: bool = typer.Option(True, "--reload/--no-reload"),
) -> None:
    """Run the FastAPI backend with uvicorn."""
    import uvicorn

    uvicorn.run("neo_ange.api.main:app", host=host, port=port, reload=reload)


@simulate_app.command("status")
def simulate_status() -> None:
    """Show Monte Carlo simulation output availability."""
    status_payload = build_simulation_pipeline().status()
    console.print(Panel.fit("Monte Carlo simulation status", title=PROJECT_NAME))
    _print_key_value_table("Simulation pipeline", status_payload)
    if not status_payload["risk_scores_available"]:
        console.print(
            "[yellow]Risk scores not found. Run: python -m neo_ange.cli risk build[/yellow]"
        )
    if not status_payload["simulation_results_available"]:
        console.print(
            "[yellow]Simulation results not found. Run: "
            "python -m neo_ange.cli simulate batch[/yellow]"
        )


@simulate_app.command("object")
def simulate_object(
    object_key: str = typer.Option(..., "--object-key"),
    n_simulations: int = typer.Option(1000, "--n-simulations", min=1),
    random_state: int = typer.Option(42, "--random-state"),
) -> None:
    """Run approximate Monte Carlo simulation for one object."""
    result = build_simulation_pipeline().simulate_object(
        object_key=object_key,
        n_simulations=n_simulations,
        random_state=random_state,
    )
    console.print(json.dumps(to_jsonable(result), indent=2, sort_keys=True))
    if result.get("status") in {"failed", "not_found"}:
        raise typer.Exit(code=1)


@simulate_app.command("batch")
def simulate_batch(
    limit: int = typer.Option(50, "--limit", min=1),
    n_simulations: int = typer.Option(500, "--n-simulations", min=1),
    random_state: int = typer.Option(42, "--random-state"),
) -> None:
    """Run approximate Monte Carlo simulation for top ranked objects."""
    result = build_simulation_pipeline().simulate_batch(
        limit=limit,
        n_simulations=n_simulations,
        random_state=random_state,
    )
    console.print(json.dumps(to_jsonable(result), indent=2, sort_keys=True))
    if result.get("status") == "failed":
        raise typer.Exit(code=1)


@simulate_app.command("latest")
def simulate_latest(object_key: str = typer.Option(..., "--object-key")) -> None:
    """Show latest saved simulation result for one object."""
    result = build_simulation_pipeline().latest_for_object(object_key)
    if result is None:
        console.print(
            "[yellow]Simulation results not found. Run: "
            "python -m neo_ange.cli simulate batch[/yellow]"
        )
        raise typer.Exit(code=1)
    console.print(json.dumps(to_jsonable(result), indent=2, sort_keys=True))


def _list_bronze_sources(bronze_root: Path) -> list[str]:
    if not bronze_root.exists():
        return []
    return sorted(
        child.name
        for child in bronze_root.iterdir()
        if child.is_dir() and any(child.rglob("*.json"))
    )


def _discover_designations(
    discovery: ObjectDiscoveryService,
    strategy: str,
    limit: int,
) -> list[str]:
    if strategy == "all":
        return discovery.discover_all(limit=limit)
    if strategy == "silver-cad":
        return discovery.discover_from_silver_cad(limit=limit)
    if strategy == "silver-sentry":
        return discovery.discover_from_silver_sentry(limit=limit)
    if strategy == "bronze-cad":
        return discovery.discover_from_bronze_cad(limit=limit)
    if strategy == "bronze-sentry":
        return discovery.discover_from_bronze_sentry(limit=limit)
    if strategy == "curated":
        return discovery.curated_seed_objects(limit=limit)
    allowed = "all, silver-cad, silver-sentry, bronze-cad, bronze-sentry, curated"
    raise typer.BadParameter(f"Unsupported strategy '{strategy}'. Expected one of: {allowed}.")


def _latest_paths(root: Path, patterns: list[str], limit: int = 5) -> list[Path]:
    if not root.exists():
        return []
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(path for path in root.glob(pattern) if path.is_file())
    return sorted(paths, key=lambda path: path.stat().st_mtime, reverse=True)[:limit]


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


def _print_key_value_table(title: str, payload: dict) -> None:
    table = Table(title=title)
    table.add_column("Key")
    table.add_column("Value", overflow="fold")
    for key, value in payload.items():
        table.add_row(str(key), json.dumps(to_jsonable(value), sort_keys=True))
    console.print(table)


if __name__ == "__main__":
    app()
