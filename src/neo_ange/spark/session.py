"""SparkSession factory for local ETL jobs."""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyspark.sql import SparkSession


def create_spark_session(
    app_name: str = "neo-ange-risk-lab",
    master: str = "local[*]",
    log_level: str = "WARN",
) -> SparkSession:
    """Create a lightweight local SparkSession for bronze/silver/gold ETL."""
    try:
        from pyspark.sql import SparkSession
    except ImportError as exc:
        message = (
            "PySpark is not installed. Install project dependencies with "
            'python -m pip install -e ".[dev]" before running ETL.'
        )
        raise RuntimeError(message) from exc

    try:
        os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
        os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)
        spark = (
            SparkSession.builder.appName(app_name)
            .master(master)
            .config("spark.pyspark.python", sys.executable)
            .config("spark.pyspark.driver.python", sys.executable)
            .config("spark.sql.session.timeZone", "UTC")
            .config("spark.ui.enabled", "false")
            .config("spark.ui.showConsoleProgress", "false")
            .config("spark.driver.bindAddress", "127.0.0.1")
            .config("spark.sql.shuffle.partitions", "8")
            .config("spark.default.parallelism", "8")
            .config("spark.sql.parquet.compression.codec", "snappy")
            .getOrCreate()
        )
        spark.sparkContext.setLogLevel(log_level.upper())
    except Exception as exc:
        message = (
            "Unable to start a local PySpark session. Verify that Java is installed "
            "and available on PATH, then retry the ETL command."
        )
        raise RuntimeError(message) from exc

    return spark


def stop_spark_session(spark: SparkSession) -> None:
    """Stop a SparkSession if it is active."""
    if spark is not None:
        spark.stop()
