"""Gold-layer storage helpers."""

from __future__ import annotations

from pathlib import Path

from neo_ange.utils.paths import ensure_directory, list_data_tables


class GoldStorage:
    """Resolve and inspect gold table and quality report paths."""

    def __init__(self, root_dir: Path | str = "data/gold") -> None:
        self.root_dir = Path(root_dir)

    def table_path(self, table_name: str) -> Path:
        return ensure_directory(self.root_dir / table_name)

    def quality_reports_path(self) -> Path:
        return ensure_directory(self.root_dir / "quality_reports")

    def list_tables(self) -> list[str]:
        return [table for table in list_data_tables(self.root_dir) if table != "quality_reports"]

    def latest_quality_reports(self, limit: int = 5) -> list[Path]:
        reports_dir = self.root_dir / "quality_reports"
        if not reports_dir.exists():
            return []
        reports = sorted(reports_dir.glob("*.json"), key=lambda path: path.name, reverse=True)
        return reports[:limit]
