"""Bulk SBDB Object ingestion using locally discovered designations."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from neo_ange.expansion.discovery import ObjectDiscoveryService
from neo_ange.manifests.run_manifest import (
    RunManifest,
    create_run_id,
    save_manifest,
    utc_now_manifest,
)
from neo_ange.services.bronze_storage import BronzeStorage

logger = logging.getLogger(__name__)


class BulkObjectIngestionService:
    """Ingest many SBDB Object payloads while tolerating per-object failures."""

    VALID_STRATEGIES = {
        "all",
        "silver-cad",
        "silver-sentry",
        "bronze-cad",
        "bronze-sentry",
        "curated",
    }

    def __init__(
        self,
        object_client: Any,
        bronze_storage: BronzeStorage,
        discovery_service: ObjectDiscoveryService,
        request_delay_seconds: float = 0.2,
    ) -> None:
        self.object_client = object_client
        self.bronze_storage = bronze_storage
        self.discovery_service = discovery_service
        self.request_delay_seconds = request_delay_seconds

    def ingest_designations(
        self,
        designations: list[str],
        limit: int | None = None,
        rich: bool = True,
        skip_existing: bool = True,
    ) -> dict[str, Any]:
        """Ingest a de-duplicated list of object designations into bronze storage."""
        started_at = utc_now_manifest()
        run_id = create_run_id("ingestion")
        warnings: list[str] = []
        failed_items: list[dict[str, str]] = []
        output_paths: list[str] = []
        unique_designations = _stable_unique(designations)
        requested = len(unique_designations if limit is None else unique_designations[:limit])
        skipped_existing = 0
        attempted = 0
        succeeded = 0

        for designation in unique_designations[:limit]:
            if skip_existing and self._object_exists(designation):
                skipped_existing += 1
                continue

            attempted += 1
            try:
                payload = self._fetch_object(designation, rich=rich)
                path = self.bronze_storage.save_json(
                    source="sbdb_object",
                    payload=payload,
                    query_params=self._client_params({"sstr": designation, "rich": rich}),
                    object_id=designation,
                )
                output_paths.append(str(path))
                succeeded += 1
                logger.info("Ingested SBDB object %s into %s", designation, path)
            except Exception as exc:
                error = str(exc)
                failed_items.append({"designation": designation, "error": error})
                logger.warning("SBDB object ingestion failed for %s: %s", designation, error)
            finally:
                if self.request_delay_seconds > 0 and attempted < requested:
                    time.sleep(self.request_delay_seconds)

        failed = len(failed_items)
        status = _status_from_counts(succeeded=succeeded, failed=failed, attempted=attempted)
        if requested == 0:
            warnings.append("No designations were provided for ingestion.")
            status = "failed"
        if skipped_existing:
            warnings.append(f"Skipped {skipped_existing} object(s) already present in bronze.")

        result: dict[str, Any] = {
            "status": status,
            "requested": requested,
            "attempted": attempted,
            "succeeded": succeeded,
            "failed": failed,
            "skipped_existing": skipped_existing,
            "output_paths": output_paths,
            "failed_items": failed_items,
            "warnings": warnings,
        }
        manifest_path = self._save_manifest(
            run_id=run_id,
            started_at=started_at,
            result=result,
            inputs={
                "designations": unique_designations[:limit],
                "limit": limit,
                "rich": rich,
                "skip_existing": skip_existing,
            },
        )
        result["manifest_path"] = str(manifest_path)
        return result

    def ingest_from_discovery(
        self,
        strategy: str = "all",
        limit: int = 100,
        rich: bool = True,
        skip_existing: bool = True,
    ) -> dict[str, Any]:
        """Discover designations with a selected strategy and ingest them."""
        designations = self._discover(strategy=strategy, limit=limit)
        result = self.ingest_designations(
            designations=designations,
            limit=limit,
            rich=rich,
            skip_existing=skip_existing,
        )
        result["strategy"] = strategy
        result["discovered"] = len(designations)
        if self.discovery_service.warnings:
            result["warnings"] = [
                *result.get("warnings", []),
                *self.discovery_service.warnings,
            ]
        return result

    def _discover(self, strategy: str, limit: int) -> list[str]:
        if strategy not in self.VALID_STRATEGIES:
            allowed = ", ".join(sorted(self.VALID_STRATEGIES))
            raise ValueError(f"Unsupported discovery strategy '{strategy}'. Expected: {allowed}.")
        if strategy == "all":
            return self.discovery_service.discover_all(limit=limit)
        if strategy == "silver-cad":
            return self.discovery_service.discover_from_silver_cad(limit=limit)
        if strategy == "silver-sentry":
            return self.discovery_service.discover_from_silver_sentry(limit=limit)
        if strategy == "bronze-cad":
            return self.discovery_service.discover_from_bronze_cad(limit=limit)
        if strategy == "bronze-sentry":
            return self.discovery_service.discover_from_bronze_sentry(limit=limit)
        return self.discovery_service.curated_seed_objects(limit=limit)

    def _fetch_object(self, designation: str, rich: bool) -> dict[str, Any]:
        if rich:
            return self.object_client.get_rich_object(designation)
        return self.object_client.get_by_designation(designation)

    def _object_exists(self, designation: str) -> bool:
        exists = getattr(self.bronze_storage, "object_exists", None)
        if callable(exists):
            return bool(exists("sbdb_object", designation))
        return False

    def _client_params(self, fallback: dict[str, Any]) -> dict[str, Any]:
        params = getattr(self.object_client, "last_request_params", None)
        if isinstance(params, dict):
            return dict(params)
        return fallback

    def _save_manifest(
        self,
        run_id: str,
        started_at: str,
        result: dict[str, Any],
        inputs: dict[str, Any],
    ) -> Path:
        manifest = RunManifest(
            run_id=run_id,
            run_type="ingestion",
            started_at_utc=started_at,
            ended_at_utc=utc_now_manifest(),
            status=result["status"],
            inputs=inputs,
            outputs={"output_paths": result["output_paths"]},
            metrics={
                "requested": result["requested"],
                "attempted": result["attempted"],
                "succeeded": result["succeeded"],
                "failed": result["failed"],
                "skipped_existing": result["skipped_existing"],
            },
            warnings=result["warnings"],
            errors=[item["error"] for item in result["failed_items"]],
        )
        return save_manifest(manifest)


def _stable_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        cleaned = str(value).strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(cleaned)
    return unique


def _status_from_counts(succeeded: int, failed: int, attempted: int) -> str:
    if failed and succeeded:
        return "partial_success"
    if failed and not succeeded:
        return "failed"
    if attempted == 0:
        return "success"
    return "success"
