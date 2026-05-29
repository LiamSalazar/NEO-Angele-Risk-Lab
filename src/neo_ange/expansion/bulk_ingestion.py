"""Bulk SBDB Object ingestion using locally discovered designations."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from neo_ange.clients.base import (
    JPLConnectionError,
    JPLHTTPError,
    JPLInvalidResponseError,
    JPLTimeoutError,
)
from neo_ange.expansion.discovery import ObjectDiscoveryService
from neo_ange.manifests.run_manifest import (
    RunManifest,
    create_run_id,
    save_manifest,
    utc_now_manifest,
)
from neo_ange.services.bronze_storage import BronzeStorage
from neo_ange.utils.serialization import write_json

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

    def ingest_max_available(
        self,
        target: int = 1000,
        rich: bool = True,
        skip_existing: bool = True,
        resume: bool = True,
        batch_size: int = 100,
        request_delay_seconds: float = 0.15,
    ) -> dict[str, Any]:
        """Discover and ingest the largest safe set of available SBDB objects."""
        started_clock = time.monotonic()
        started_at = utc_now_manifest()
        run_id = create_run_id("expansion")
        target = max(int(target), 0)
        batch_size = max(int(batch_size), 1)
        self.request_delay_seconds = max(float(request_delay_seconds), 0.0)
        warnings: list[str] = []
        failed_items: list[dict[str, str]] = []
        output_paths: list[str] = []
        checkpoint_paths: list[str] = []
        batch_manifest_paths: list[str] = []
        failure_classification_counts: dict[str, int] = {}

        designations = self.discovery_service.discover_max_available(target=target)
        if self.discovery_service.warnings:
            warnings.extend(self.discovery_service.warnings)
        resumed_successes = self._load_resume_successes() if resume else set()

        attempted = 0
        succeeded = 0
        skipped_existing = 0
        successful_objects: list[str] = []
        batch_records: list[dict[str, Any]] = []

        for index, designation in enumerate(designations, start=1):
            if resume and designation.lower() in resumed_successes:
                skipped_existing += 1
                batch_records.append(
                    {
                        "object_id": designation,
                        "status": "skipped_existing",
                        "reason": "resume_checkpoint",
                    }
                )
                continue
            if skip_existing and self._object_exists(designation):
                skipped_existing += 1
                batch_records.append(
                    {
                        "object_id": designation,
                        "status": "skipped_existing",
                        "reason": "bronze_exists",
                    }
                )
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
                successful_objects.append(designation)
                batch_records.append(
                    {"object_id": designation, "status": "success", "path": str(path)}
                )
                succeeded += 1
            except Exception as exc:
                classification = _classify_failure(exc)
                failure_classification_counts[classification] = (
                    failure_classification_counts.get(classification, 0) + 1
                )
                error = str(exc)
                failed_items.append(
                    {
                        "object_id": designation,
                        "error": error,
                        "classification": classification,
                    }
                )
                batch_records.append(
                    {
                        "object_id": designation,
                        "status": "failed",
                        "error": error,
                        "classification": classification,
                    }
                )
                logger.warning("SBDB object ingestion failed for %s: %s", designation, error)
            finally:
                should_sleep = (
                    self.request_delay_seconds > 0
                    and index < len(designations)
                    and attempted + skipped_existing < len(designations)
                )
                if should_sleep:
                    time.sleep(self.request_delay_seconds)

            if attempted and attempted % 50 == 0:
                checkpoint_paths.append(
                    str(
                        self._save_checkpoint(
                            run_id=run_id,
                            target=target,
                            successful_objects=successful_objects,
                            failed_items=failed_items,
                            skipped_existing=skipped_existing,
                        )
                    )
                )
            if len(batch_records) >= batch_size:
                batch_manifest_paths.append(
                    str(
                        self._save_batch_manifest(
                            run_id=run_id,
                            batch_index=len(batch_manifest_paths) + 1,
                            records=batch_records,
                        )
                    )
                )
                batch_records = []

        if batch_records:
            batch_manifest_paths.append(
                str(
                    self._save_batch_manifest(
                        run_id=run_id,
                        batch_index=len(batch_manifest_paths) + 1,
                        records=batch_records,
                    )
                )
            )
        checkpoint_paths.append(
            str(
                self._save_checkpoint(
                    run_id=run_id,
                    target=target,
                    successful_objects=successful_objects,
                    failed_items=failed_items,
                    skipped_existing=skipped_existing,
                )
            )
        )

        failed = len(failed_items)
        status = _status_from_counts(succeeded=succeeded, failed=failed, attempted=attempted)
        if not designations:
            status = "failed"
            warnings.append("No objects were discovered for max expansion.")
        elapsed_seconds = time.monotonic() - started_clock
        estimated_coverage = (succeeded + skipped_existing) / target if target else 0.0
        result: dict[str, Any] = {
            "status": status,
            "target": target,
            "discovered": len(designations),
            "attempted": attempted,
            "succeeded": succeeded,
            "failed": failed,
            "skipped_existing": skipped_existing,
            "elapsed_seconds": round(elapsed_seconds, 6),
            "estimated_coverage": round(estimated_coverage, 6),
            "source_counts": dict(self.discovery_service.source_counts),
            "output_paths": output_paths,
            "failed_items": failed_items,
            "failure_classification_counts": failure_classification_counts,
            "warnings": warnings,
            "checkpoint_paths": checkpoint_paths,
            "batch_manifest_paths": batch_manifest_paths,
        }
        manifest_path = self._save_manifest(
            run_id=run_id,
            started_at=started_at,
            result=result,
            inputs={
                "target": target,
                "rich": rich,
                "skip_existing": skip_existing,
                "resume": resume,
                "batch_size": batch_size,
                "request_delay_seconds": request_delay_seconds,
            },
        )
        result["manifest_path"] = str(manifest_path)
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
                "requested": result.get("requested", result.get("target")),
                "discovered": result.get("discovered"),
                "attempted": result["attempted"],
                "succeeded": result["succeeded"],
                "failed": result["failed"],
                "skipped_existing": result["skipped_existing"],
                "estimated_coverage": result.get("estimated_coverage"),
            },
            warnings=result["warnings"],
            errors=[item["error"] for item in result["failed_items"]],
        )
        return save_manifest(manifest)

    def _save_checkpoint(
        self,
        run_id: str,
        target: int,
        successful_objects: list[str],
        failed_items: list[dict[str, str]],
        skipped_existing: int,
    ) -> Path:
        timestamp = run_id.rsplit("_", 1)[-1]
        path = Path("reports/manifests") / f"expansion_checkpoint_{timestamp}.json"
        return write_json(
            {
                "run_id": run_id,
                "target": target,
                "successful_objects": successful_objects,
                "failed_items": failed_items,
                "skipped_existing": skipped_existing,
                "updated_at_utc": utc_now_manifest(),
            },
            path,
        )

    def _save_batch_manifest(
        self,
        run_id: str,
        batch_index: int,
        records: list[dict[str, Any]],
    ) -> Path:
        timestamp = run_id.rsplit("_", 1)[-1]
        path = Path("reports/manifests") / f"expansion_batch_{timestamp}_{batch_index:04d}.json"
        return write_json(
            {
                "run_id": run_id,
                "batch_index": batch_index,
                "records": records,
                "created_at_utc": utc_now_manifest(),
            },
            path,
        )

    def _load_resume_successes(self) -> set[str]:
        successes: set[str] = set()
        manifest_dir = Path("reports/manifests")
        if not manifest_dir.exists():
            return successes
        for path in sorted(manifest_dir.glob("expansion_checkpoint_*.json")):
            try:
                import json

                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            for value in payload.get("successful_objects", []):
                cleaned = str(value).strip().lower()
                if cleaned:
                    successes.add(cleaned)
        return successes


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


def _classify_failure(exc: Exception) -> str:
    if isinstance(exc, JPLHTTPError):
        return "http_error"
    if isinstance(exc, JPLTimeoutError):
        return "timeout"
    if isinstance(exc, JPLConnectionError):
        return "connection_error"
    if isinstance(exc, JPLInvalidResponseError):
        return "invalid_response"
    return "unknown_error"
