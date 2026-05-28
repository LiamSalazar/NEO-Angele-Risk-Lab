"""Silver-layer storage helpers."""

from __future__ import annotations

from pathlib import Path

from neo_ange.utils.paths import ensure_directory, list_data_tables


class SilverStorage:
    """Resolve and inspect silver table paths."""

    def __init__(self, root_dir: Path | str = "data/silver") -> None:
        self.root_dir = Path(root_dir)

    def table_path(self, table_name: str) -> Path:
        return ensure_directory(self.root_dir / table_name)

    def list_tables(self) -> list[str]:
        return list_data_tables(self.root_dir)
