from __future__ import annotations

from neo_ange.pipelines.ingestion import IngestionPipeline
from neo_ange.services.bronze_storage import BronzeStorage


class FakeSBDBQueryClient:
    last_request_params = {"fields": "spkid", "limit": 100}

    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail

    def query_neos(self, limit: int = 100) -> dict:
        if self.should_fail:
            raise RuntimeError("query failed")
        self.last_request_params = {"fields": "spkid", "limit": limit}
        return {"signature": {"source": "SBDB Query"}, "data": []}


class FakeSBDBObjectClient:
    last_request_params = {"sstr": "99942"}

    def get_rich_object(self, designation_or_name: str) -> dict:
        self.last_request_params = {"sstr": designation_or_name, "phys-par": 1}
        return {"signature": {"source": "SBDB Object"}, "object": {"des": designation_or_name}}

    def get_by_search_string(self, designation_or_name: str) -> dict:
        self.last_request_params = {"sstr": designation_or_name}
        return {"signature": {"source": "SBDB Object"}, "object": {"des": designation_or_name}}


class FakeCADClient:
    last_request_params = {"date-min": "now"}

    def query(self, **kwargs) -> dict:
        self.last_request_params = kwargs
        return {"signature": {"source": "CAD"}, "data": []}


class FakeSentryClient:
    last_request_params = {}

    def get_summary(self) -> dict:
        self.last_request_params = {}
        return {"signature": {"source": "Sentry"}, "data": []}

    def get_virtual_impactors(self, ip_min=None) -> dict:
        self.last_request_params = {"all": 1, "ip-min": ip_min}
        return {"signature": {"source": "Sentry"}, "data": []}


def build_pipeline(tmp_path, query_should_fail: bool = False) -> IngestionPipeline:
    return IngestionPipeline(
        sbdb_query_client=FakeSBDBQueryClient(should_fail=query_should_fail),
        sbdb_object_client=FakeSBDBObjectClient(),
        close_approach_client=FakeCADClient(),
        sentry_client=FakeSentryClient(),
        bronze_storage=BronzeStorage(tmp_path),
    )


def test_ingest_sample_bundle_continues_when_one_source_fails(tmp_path) -> None:
    pipeline = build_pipeline(tmp_path, query_should_fail=True)

    paths = pipeline.ingest_sample_bundle()

    assert len(paths) == 3
    assert all(path.exists() for path in paths)


def test_ingest_object_saves_mock_response(tmp_path) -> None:
    pipeline = build_pipeline(tmp_path)

    path = pipeline.ingest_object("99942")

    assert path.exists()
    assert "sbdb_object" in str(path)


def test_ingest_cad_sample_saves_mock_response(tmp_path) -> None:
    pipeline = build_pipeline(tmp_path)

    path = pipeline.ingest_cad_sample(limit=5)

    assert path.exists()
    assert "cad" in str(path)
