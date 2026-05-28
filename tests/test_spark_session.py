from __future__ import annotations


def test_create_spark_session_creates_session(spark) -> None:
    assert spark.sparkContext.appName == "neo-ange-risk-lab-test"
    assert spark.range(1).count() == 1


def test_stop_spark_session_function_is_available(spark) -> None:
    assert spark.sparkContext is not None
