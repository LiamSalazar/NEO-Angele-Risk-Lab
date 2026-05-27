"""Bronze-layer JSON storage service."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from neo_ange.domain.models import BronzeRecord, IngestionMetadata
from neo_ange.utils.time import current_utc_date_partition, utc_now_iso, utc_timestamp_compact


class BronzeStorage:
    """Persist raw source responses under date-partitioned bronze paths."""

    def __init__(self, root_dir: Path | str = "data/bronze") -> None:
        self.root_dir = Path(root_dir)

    def save_json(
        self,
        source: str,
        payload: dict[str, Any],
        query_params: dict[str, Any] | None = None,
        object_id: str | None = None,
    ) -> Path:
        safe_source = self._slugify(source)
        ingest_date = current_utc_date_partition()
        timestamp = utc_timestamp_compact()
        slug = self._slugify(object_id or ("query" if query_params else "sample"))
        output_dir = self.root_dir / safe_source / f"ingest_date={ingest_date}"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{timestamp}_{slug}.json"

        metadata = IngestionMetadata(
            source=safe_source,
            ingested_at_utc=utc_now_iso(),
            query_params=query_params or {},
            object_id=object_id,
            api_signature=payload.get("signature", {}),
        )
        record = BronzeRecord(metadata=metadata, data=payload)
        output_path.write_text(
            json.dumps(record.model_dump(mode="json"), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return output_path

    def list_files(self, source: str | None = None) -> list[Path]:
        search_root = self.root_dir / self._slugify(source) if source else self.root_dir
        if not search_root.exists():
            return []
        return sorted(path for path in search_root.rglob("*.json") if path.is_file())

    def latest_file(self, source: str) -> Path | None:
        files = self.list_files(source)
        if not files:
            return None
        return max(files, key=lambda path: str(path))

    @staticmethod
    def _slugify(value: str) -> str:
        slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip().lower())
        slug = re.sub(r"_+", "_", slug).strip("._-")
        return slug or "sample"
