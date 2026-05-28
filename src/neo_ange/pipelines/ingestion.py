"""Ingestion pipeline for landing NASA/JPL responses in bronze storage."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from neo_ange.clients.close_approach import CloseApproachClient
from neo_ange.clients.sbdb_object import SBDBObjectClient
from neo_ange.clients.sbdb_query import SBDBQueryClient
from neo_ange.clients.sentry import SentryClient
from neo_ange.expansion.bulk_ingestion import BulkObjectIngestionService
from neo_ange.expansion.discovery import ObjectDiscoveryService
from neo_ange.services.bronze_storage import BronzeStorage
from neo_ange.utils.config import get_settings

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """Coordinate API clients and bronze persistence."""

    def __init__(
        self,
        sbdb_query_client: SBDBQueryClient | None = None,
        sbdb_object_client: SBDBObjectClient | None = None,
        close_approach_client: CloseApproachClient | None = None,
        sentry_client: SentryClient | None = None,
        bronze_storage: BronzeStorage | None = None,
    ) -> None:
        settings = get_settings()
        self.sbdb_query_client = sbdb_query_client or SBDBQueryClient(
            timeout=settings.request_timeout
        )
        self.sbdb_object_client = sbdb_object_client or SBDBObjectClient(
            timeout=settings.request_timeout
        )
        self.close_approach_client = close_approach_client or CloseApproachClient(
            timeout=settings.request_timeout
        )
        self.sentry_client = sentry_client or SentryClient(timeout=settings.request_timeout)
        self.bronze_storage = bronze_storage or BronzeStorage(Path(settings.data_dir) / "bronze")
        self.last_failures: list[tuple[str, str]] = []

    def ingest_sbdb_query_sample(self, limit: int = 100) -> Path:
        payload = self.sbdb_query_client.query_neos(limit=limit)
        return self.bronze_storage.save_json(
            source="sbdb_query",
            payload=payload,
            query_params=self._client_params(self.sbdb_query_client, {"limit": limit}),
        )

    def ingest_object(self, designation_or_name: str, rich: bool = True) -> Path:
        if rich:
            payload = self.sbdb_object_client.get_rich_object(designation_or_name)
        else:
            payload = self.sbdb_object_client.get_by_search_string(designation_or_name)
        return self.bronze_storage.save_json(
            source="sbdb_object",
            payload=payload,
            query_params=self._client_params(
                self.sbdb_object_client,
                {"sstr": designation_or_name, "rich": rich},
            ),
            object_id=designation_or_name,
        )

    def ingest_cad_sample(
        self,
        date_min: str = "now",
        date_max: str = "+60",
        dist_max: str = "0.05",
        limit: int = 100,
    ) -> Path:
        payload = self.close_approach_client.query(
            date_min=date_min,
            date_max=date_max,
            dist_max=dist_max,
            limit=limit,
        )
        return self.bronze_storage.save_json(
            source="cad",
            payload=payload,
            query_params=self._client_params(
                self.close_approach_client,
                {
                    "date-min": date_min,
                    "date-max": date_max,
                    "dist-max": dist_max,
                    "limit": limit,
                },
            ),
        )

    def ingest_sentry_summary(self) -> Path:
        payload = self.sentry_client.get_summary()
        return self.bronze_storage.save_json(
            source="sentry",
            payload=payload,
            query_params=self._client_params(self.sentry_client, {}),
            object_id="summary",
        )

    def ingest_sentry_virtual_impactors(self, ip_min: float | None = None) -> Path:
        payload = self.sentry_client.get_virtual_impactors(ip_min=ip_min)
        fallback = {"all": 1}
        if ip_min is not None:
            fallback["ip-min"] = ip_min
        return self.bronze_storage.save_json(
            source="sentry",
            payload=payload,
            query_params=self._client_params(self.sentry_client, fallback),
            object_id="virtual_impactors",
        )

    def ingest_sample_bundle(self) -> list[Path]:
        successes: list[Path] = []
        failures: list[tuple[str, str]] = []
        self.last_failures = failures
        tasks: list[tuple[str, Callable[[], Path]]] = [
            ("sbdb_query", lambda: self.ingest_sbdb_query_sample(limit=100)),
            ("cad", lambda: self.ingest_cad_sample(limit=100)),
            ("sentry_summary", self.ingest_sentry_summary),
            ("sbdb_object", lambda: self.ingest_object("99942", rich=True)),
        ]

        for name, task in tasks:
            try:
                path = task()
                successes.append(path)
                logger.info("Ingested %s into %s", name, path)
            except Exception as exc:
                failures.append((name, str(exc)))
                logger.warning("Ingestion task failed but bundle will continue: %s", name)
                logger.debug("Sample bundle failure details", exc_info=True)

        if failures:
            logger.warning(
                "Sample bundle completed with %s failure(s).",
                len(failures),
            )
        return successes

    def ingest_discovered_objects(
        self,
        strategy: str = "all",
        limit: int = 100,
        rich: bool = True,
        skip_existing: bool = True,
        request_delay_seconds: float = 0.2,
    ) -> dict[str, Any]:
        """Discover object designations from local data and ingest SBDB Object payloads."""
        settings = get_settings()
        service = BulkObjectIngestionService(
            object_client=self.sbdb_object_client,
            bronze_storage=self.bronze_storage,
            discovery_service=ObjectDiscoveryService(
                silver_root=settings.silver_dir,
                bronze_root=Path(settings.data_dir) / "bronze",
            ),
            request_delay_seconds=request_delay_seconds,
        )
        return service.ingest_from_discovery(
            strategy=strategy,
            limit=limit,
            rich=rich,
            skip_existing=skip_existing,
        )

    @staticmethod
    def _client_params(client: Any, fallback: dict[str, Any]) -> dict[str, Any]:
        params = getattr(client, "last_request_params", None)
        if isinstance(params, dict):
            return dict(params)
        return fallback
