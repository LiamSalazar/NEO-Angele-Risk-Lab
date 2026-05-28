"""Path helpers shared by storage, Spark readers, and CLI status."""

from __future__ import annotations

from pathlib import Path


def ensure_directory(path: Path | str) -> Path:
    """Create a directory if needed and return it as a Path."""
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def to_spark_path(path: Path | str) -> str:
    """Return a local path string that Spark accepts on Windows, Linux, and macOS."""
    return Path(path).resolve().as_posix()


def contains_files(path: Path | str, pattern: str = "*") -> bool:
    root = Path(path)
    return root.exists() and any(child.is_file() for child in root.rglob(pattern))


def list_data_tables(root: Path | str) -> list[str]:
    """List child directories that contain at least one data file."""
    root_path = Path(root)
    if not root_path.exists():
        return []
    return sorted(
        child.name for child in root_path.iterdir() if child.is_dir() and contains_files(child)
    )
