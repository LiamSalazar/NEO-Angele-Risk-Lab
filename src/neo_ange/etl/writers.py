"""Parquet writers for silver and gold tables."""

from __future__ import annotations

import logging
import os
import shutil
import sys
import uuid
from pathlib import Path
from typing import Any

from pyspark.sql import DataFrame

from neo_ange.utils.paths import ensure_directory, to_spark_path

logger = logging.getLogger(__name__)


class ParquetTableWriter:
    """Write Spark DataFrames as Parquet tables with simple lineage summaries."""

    def write(
        self,
        df: DataFrame,
        output_path: str | Path,
        mode: str = "overwrite",
        skip_empty: bool = True,
    ) -> dict[str, Any]:
        path = ensure_directory(output_path)
        is_empty = len(df.take(1)) == 0
        if is_empty and skip_empty:
            logger.warning("Skipping empty Parquet write to %s", path)
            return {
                "path": str(path),
                "mode": mode,
                "row_count": 0,
                "status": "skipped_empty",
            }

        if _prefer_pyarrow_local_write():
            row_count = _write_with_pyarrow(df, path, mode)
            logger.info("Wrote %s row(s) to %s with PyArrow", row_count, path)
            return {
                "path": str(path),
                "mode": mode,
                "row_count": row_count,
                "status": "written_pyarrow",
            }

        row_count = df.count()
        status = "written"
        try:
            df.write.mode(mode).parquet(to_spark_path(path))
        except Exception as exc:
            if not _is_windows_hadoop_home_error(exc):
                raise
            logger.warning(
                "Spark local Parquet write hit the Windows Hadoop home/winutils issue; "
                "falling back to PyArrow for %s.",
                path,
            )
            _write_with_pyarrow(df, path, mode)
            status = "written_pyarrow"
        logger.info("Wrote %s row(s) to %s", row_count, path)
        return {
            "path": str(path),
            "mode": mode,
            "row_count": row_count,
            "status": status,
        }


def _is_windows_hadoop_home_error(exc: Exception) -> bool:
    text = str(exc)
    return "HADOOP_HOME" in text or "hadoop.home.dir" in text or "winutils" in text


def _prefer_pyarrow_local_write() -> bool:
    return sys.platform == "win32" and not (
        os.environ.get("HADOOP_HOME") or os.environ.get("hadoop.home.dir")
    )


def _write_with_pyarrow(df: DataFrame, path: Path, mode: str) -> int:
    import pyarrow as pa
    import pyarrow.parquet as pq

    if mode == "overwrite":
        _clear_directory(path)
    elif mode != "append" and any(path.glob("*.parquet")):
        raise FileExistsError(f"Output path already contains Parquet files: {path}")

    path.mkdir(parents=True, exist_ok=True)
    pandas_df = df.toPandas()
    table = pa.Table.from_pandas(pandas_df, preserve_index=False)
    pq.write_table(table, path / f"part-{uuid.uuid4().hex}.parquet")
    (path / "_SUCCESS").write_text("", encoding="utf-8")
    return len(pandas_df)


def _clear_directory(path: Path) -> None:
    resolved = path.resolve()
    if not resolved.exists():
        resolved.mkdir(parents=True, exist_ok=True)
        return
    for child in resolved.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
