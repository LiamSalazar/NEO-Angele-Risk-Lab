"""Base client for public NASA/JPL JSON APIs."""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)

USER_AGENT = "neo-ange-risk-lab/0.1"


class JPLClientError(RuntimeError):
    """Base exception for JPL client failures."""


class JPLHTTPError(JPLClientError):
    """Raised when an API returns a non-success HTTP status."""


class JPLTimeoutError(JPLClientError):
    """Raised when a request times out."""


class JPLConnectionError(JPLClientError):
    """Raised when a network connection fails."""


class JPLInvalidResponseError(JPLClientError):
    """Raised when an API response is empty or not valid JSON."""


class JPLSchemaWarning(JPLClientError):
    """Raised when a strict schema expectation is violated."""


class BaseJPLClient:
    """Small typed wrapper around a public NASA/JPL JSON endpoint."""

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        session: requests.Session | None = None,
        validate_signature: bool = False,
        max_retries: int = 2,
        backoff_seconds: float = 0.5,
    ) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.session = session or requests.Session()
        self.validate_signature = validate_signature
        self.max_retries = max(0, int(max_retries))
        self.backoff_seconds = max(float(backoff_seconds), 0.0)
        self.last_request_params: dict[str, Any] = {}
        self.last_request_url: str = base_url
        self.last_error_type: str | None = None
        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": USER_AGENT,
            }
        )

    def build_url(self, params: dict[str, Any] | None = None) -> str:
        """Return the prepared URL used for debugging and metadata."""
        request = requests.Request("GET", self.base_url, params=params or {})
        return request.prepare().url or self.base_url

    def get(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute a GET request and return a parsed JSON object."""
        request_params = params or {}
        self.last_request_params = dict(request_params)
        self.last_request_url = self.build_url(request_params)
        logger.debug("Requesting JPL API: %s", self.last_request_url)

        response = None
        attempts = self.max_retries + 1
        for attempt in range(attempts):
            try:
                response = self.session.get(
                    self.base_url,
                    params=request_params,
                    timeout=self.timeout,
                )
            except requests.Timeout as exc:
                self.last_error_type = "timeout"
                if attempt < self.max_retries:
                    self._sleep_before_retry(attempt)
                    continue
                msg = f"Request to {self.base_url} timed out after {self.timeout} seconds."
                raise JPLTimeoutError(msg) from exc
            except requests.ConnectionError as exc:
                self.last_error_type = "server_error"
                if attempt < self.max_retries:
                    self._sleep_before_retry(attempt)
                    continue
                msg = f"Could not connect to {self.base_url}: {exc}"
                raise JPLConnectionError(msg) from exc
            except requests.RequestException as exc:
                self.last_error_type = "server_error"
                if attempt < self.max_retries:
                    self._sleep_before_retry(attempt)
                    continue
                msg = f"Request to {self.base_url} failed: {exc}"
                raise JPLClientError(msg) from exc

            if response.status_code >= 500 and attempt < self.max_retries:
                self.last_error_type = "server_error"
                self._sleep_before_retry(attempt)
                continue
            break

        if response is None:
            self.last_error_type = "server_error"
            raise JPLClientError(f"Request to {self.base_url} failed before receiving a response.")

        if response.status_code >= 400:
            self.last_error_type = "client_error" if response.status_code < 500 else "server_error"
            detail = response.text.strip() or "No response body."
            msg = (
                f"JPL API returned HTTP {response.status_code} "
                f"for {self.last_request_url}: {detail}"
            )
            raise JPLHTTPError(msg)

        if not response.text or not response.text.strip():
            self.last_error_type = "invalid_json"
            msg = f"JPL API returned an empty response for {self.last_request_url}."
            raise JPLInvalidResponseError(msg)

        try:
            payload = response.json()
        except ValueError as exc:
            self.last_error_type = "invalid_json"
            msg = f"JPL API returned invalid JSON for {self.last_request_url}."
            raise JPLInvalidResponseError(msg) from exc

        if not isinstance(payload, dict):
            self.last_error_type = "schema_warning"
            msg = f"JPL API returned JSON that is not an object for {self.last_request_url}."
            raise JPLInvalidResponseError(msg)

        if self.validate_signature and "signature" not in payload:
            self.last_error_type = "schema_warning"
            msg = f"JPL API response did not include a signature for {self.last_request_url}."
            raise JPLInvalidResponseError(msg)

        self.last_error_type = None
        return payload

    def _sleep_before_retry(self, attempt: int) -> None:
        delay = self.backoff_seconds * (2**attempt)
        if delay > 0:
            time.sleep(delay)
