from __future__ import annotations

from pathlib import Path

from neo_ange.expansion.bulk_ingestion import BulkObjectIngestionService
from neo_ange.expansion.discovery import ObjectDiscoveryService
from neo_ange.services.bronze_storage import BronzeStorage


class FakeObjectClient:
    def __init__(self) -> None:
        self.last_request_params = {}

    def get_rich_object(self, designation: str) -> dict:
        self.last_request_params = {"sstr": designation, "rich": True}
        if designation == "bad":
            raise RuntimeError("not found")
        return {"signature": {"source": "SBDB"}, "object": {"des": designation}}

    def get_by_designation(self, designation: str) -> dict:
        self.last_request_params = {"des": designation}
        return {"signature": {"source": "SBDB"}, "object": {"des": designation}}


def test_bulk_ingestion_continues_and_saves_manifest(tmp_path, monkeypatch) -> None:
    manifest_path = tmp_path / "manifest.json"

    def fake_save_manifest(manifest, output_dir="reports/manifests") -> Path:
        manifest_path.write_text(manifest.status, encoding="utf-8")
        return manifest_path

    monkeypatch.setattr("neo_ange.expansion.bulk_ingestion.save_manifest", fake_save_manifest)
    storage = BronzeStorage(tmp_path / "bronze")
    service = BulkObjectIngestionService(
        object_client=FakeObjectClient(),
        bronze_storage=storage,
        discovery_service=ObjectDiscoveryService(tmp_path / "silver", tmp_path / "bronze"),
        request_delay_seconds=0,
    )

    result = service.ingest_designations(["ok", "bad", "ok"], rich=True)

    assert result["status"] == "partial_success"
    assert result["requested"] == 2
    assert result["attempted"] == 2
    assert result["succeeded"] == 1
    assert result["failed"] == 1
    assert result["manifest_path"] == str(manifest_path)
    assert storage.object_exists("sbdb_object", "ok")


def test_bulk_ingestion_respects_skip_existing(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "neo_ange.expansion.bulk_ingestion.save_manifest",
        lambda manifest, output_dir="reports/manifests": tmp_path / "manifest.json",
    )
    storage = BronzeStorage(tmp_path / "bronze")
    storage.save_json("sbdb_object", {"signature": {}}, object_id="99942")
    service = BulkObjectIngestionService(
        object_client=FakeObjectClient(),
        bronze_storage=storage,
        discovery_service=ObjectDiscoveryService(tmp_path / "silver", tmp_path / "bronze"),
        request_delay_seconds=0,
    )

    result = service.ingest_designations(["99942"], skip_existing=True)

    assert result["status"] == "success"
    assert result["attempted"] == 0
    assert result["skipped_existing"] == 1
