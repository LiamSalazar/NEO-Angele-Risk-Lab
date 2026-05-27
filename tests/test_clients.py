from __future__ import annotations

import pytest
import requests

from neo_ange.clients.base import (
    BaseJPLClient,
    JPLHTTPError,
    JPLInvalidResponseError,
    JPLTimeoutError,
)
from neo_ange.clients.close_approach import CloseApproachClient
from neo_ange.clients.sbdb_object import SBDBObjectClient
from neo_ange.clients.sbdb_query import SBDBQueryClient
from neo_ange.clients.sentry import SentryClient


class FakeResponse:
    def __init__(
        self,
        status_code: int = 200,
        payload: dict | None = None,
        text: str = '{"ok": true}',
        json_error: bool = False,
    ) -> None:
        self.status_code = status_code
        self._payload = payload or {"ok": True}
        self.text = text
        self.json_error = json_error

    def json(self) -> dict:
        if self.json_error:
            raise ValueError("invalid json")
        return self._payload


class FakeSession:
    def __init__(
        self, response: FakeResponse | None = None, error: Exception | None = None
    ) -> None:
        self.response = response or FakeResponse()
        self.error = error
        self.headers: dict[str, str] = {}
        self.calls: list[dict] = []

    def get(self, url: str, params: dict | None = None, timeout: int | None = None) -> FakeResponse:
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        if self.error:
            raise self.error
        return self.response


def test_base_client_processes_valid_json() -> None:
    session = FakeSession(FakeResponse(payload={"signature": {"version": "1"}, "data": []}))
    client = BaseJPLClient("https://example.test/api", session=session, validate_signature=True)

    payload = client.get({"a": "b"})

    assert payload["signature"]["version"] == "1"
    assert client.last_request_params == {"a": "b"}
    assert "a=b" in client.last_request_url


def test_base_client_handles_http_error() -> None:
    session = FakeSession(FakeResponse(status_code=500, text="server unavailable"))
    client = BaseJPLClient("https://example.test/api", session=session)

    with pytest.raises(JPLHTTPError, match="HTTP 500"):
        client.get()


def test_base_client_handles_timeout() -> None:
    session = FakeSession(error=requests.Timeout("too slow"))
    client = BaseJPLClient("https://example.test/api", timeout=1, session=session)

    with pytest.raises(JPLTimeoutError, match="timed out"):
        client.get()


def test_base_client_handles_invalid_json() -> None:
    session = FakeSession(FakeResponse(text="not json", json_error=True))
    client = BaseJPLClient("https://example.test/api", session=session)

    with pytest.raises(JPLInvalidResponseError, match="invalid JSON"):
        client.get()


def test_sbdb_object_client_validates_covariance_format() -> None:
    client = SBDBObjectClient()

    with pytest.raises(ValueError, match="covariance_format"):
        client.get_with_covariance("99942", covariance_format="xml")


def test_sentry_client_keeps_modes_separate(monkeypatch: pytest.MonkeyPatch) -> None:
    client = SentryClient()
    calls: list[dict] = []

    def fake_get(params: dict | None = None) -> dict:
        calls.append(params or {})
        return {"ok": True}

    monkeypatch.setattr(client, "get", fake_get)

    client.get_summary()
    client.get_object_by_designation("99942")
    client.get_virtual_impactors(ip_min=1e-6)
    client.get_removed_objects()

    assert calls == [{}, {"des": "99942"}, {"all": 1, "ip-min": 1e-6}, {"removed": 1}]


def test_sbdb_query_client_deduplicates_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    client = SBDBQueryClient()
    captured: dict = {}

    def fake_get(params: dict | None = None) -> dict:
        captured.update(params or {})
        return {"ok": True}

    monkeypatch.setattr(client, "get", fake_get)

    client.query_custom(["spkid", "spkid", "neo", " neo "], limit=10)

    assert captured["fields"] == "spkid,neo"
    assert captured["limit"] == 10


def test_close_approach_client_builds_expected_params(monkeypatch: pytest.MonkeyPatch) -> None:
    client = CloseApproachClient()
    captured: dict = {}

    def fake_get(params: dict | None = None) -> dict:
        captured.update(params or {})
        return {"ok": True}

    monkeypatch.setattr(client, "get", fake_get)

    client.query(date_min="now", date_max="+60", dist_max="0.05", pha=True, limit=20)

    assert captured["date-max"] == "+60"
    assert captured["neo"] == "true"
    assert captured["pha"] == "true"
    assert captured["limit"] == 20
    assert captured["diameter"] == "true"
    assert captured["fullname"] == "true"
