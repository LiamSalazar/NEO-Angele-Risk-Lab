"""Spark integration helpers."""

from neo_ange.spark.session import create_spark_session, stop_spark_session

__all__ = ["create_spark_session", "stop_spark_session"]
