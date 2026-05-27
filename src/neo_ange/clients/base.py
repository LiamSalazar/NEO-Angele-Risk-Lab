"""Base client for public NASA/JPL JSON APIs."""

from __future__ import annotations

import logging
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


class BaseJPLClient:
    """Small typed wrapper around a public NASA/JPL JSON endpoint."""

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        session: requests.Session | None = None,
        validate_signature: bool = False,
    ) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.session = session or requests.Session()
        self.validate_signature = validate_signature
        self.last_request_params: dict[str, Any] = {}
        self.last_request_url: str = base_url
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

        try:
            response = self.session.get(
                self.base_url,
                params=request_params,
                timeout=self.timeout,
            )
        except requests.Timeout as exc:
            msg = f"Request to {self.base_url} timed out after {self.timeout} seconds."
            raise JPLTimeoutError(msg) from exc
        except requests.ConnectionError as exc:
            msg = f"Could not connect to {self.base_url}: {exc}"
            raise JPLConnectionError(msg) from exc
        except requests.RequestException as exc:
            msg = f"Request to {self.base_url} failed: {exc}"
            raise JPLClientError(msg) from exc

        if response.status_code >= 400:
            detail = response.text.strip() or "No response body."
            msg = (
                f"JPL API returned HTTP {response.status_code} "
                f"for {self.last_request_url}: {detail}"
            )
            raise JPLHTTPError(msg)

        if not response.text or not response.text.strip():
            msg = f"JPL API returned an empty response for {self.last_request_url}."
            raise JPLInvalidResponseError(msg)

        try:
            payload = response.json()
        except ValueError as exc:
            msg = f"JPL API returned invalid JSON for {self.last_request_url}."
            raise JPLInvalidResponseError(msg) from exc

        if not isinstance(payload, dict):
            msg = f"JPL API returned JSON that is not an object for {self.last_request_url}."
            raise JPLInvalidResponseError(msg)

        if self.validate_signature and "signature" not in payload:
            msg = f"JPL API response did not include a signature for {self.last_request_url}."
            raise JPLInvalidResponseError(msg)

        return payload
