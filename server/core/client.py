"""
Async HTTP client for the Yelp Fusion v3 API.

Handles:
  - Bearer token auth
  - JSON deserialization
  - HTTP error → typed exception mapping
  - Tenacity retry on 429 and 5xx
"""

from __future__ import annotations

import httpx
import structlog
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from server.core.config import Settings

logger = structlog.get_logger(__name__)


# ── Internal exceptions (retryable vs non-retryable) ─────────────────────────

class YelpAPIError(Exception):
    """Base for all Yelp API errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class YelpRateLimitError(YelpAPIError):
    """HTTP 429 — too many requests (retryable)."""


class YelpServerError(YelpAPIError):
    """HTTP 5xx — server-side failure (retryable)."""


class YelpNotFoundError(YelpAPIError):
    """HTTP 404 — resource not found (not retryable)."""


class YelpAuthError(YelpAPIError):
    """HTTP 401/403 — bad or missing API key (not retryable)."""


class YelpValidationError(YelpAPIError):
    """HTTP 400 — bad request parameters (not retryable)."""


# ── Retry helpers ─────────────────────────────────────────────────────────────

def _before_sleep(retry_state: RetryCallState) -> None:
    exc = retry_state.outcome.exception() if retry_state.outcome else None
    logger.warning(
        "yelp_api_retry",
        attempt=retry_state.attempt_number,
        error=str(exc),
        wait_seconds=getattr(retry_state.next_action, "sleep", None),
    )


# ── Client ────────────────────────────────────────────────────────────────────

class YelpClient:
    """Thin async wrapper around the Yelp Fusion v3 REST API."""

    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.yelp_base_url.rstrip("/")
        self._timeout = settings.http_timeout
        self._max_retries = settings.http_max_retries
        self._wait_min = settings.http_retry_wait_min
        self._wait_max = settings.http_retry_wait_max
        self._headers = {
            "Authorization": f"Bearer {settings.yelp_api_key}",
            "Accept": "application/json",
        }

    async def get(
        self,
        path: str,
        *,
        params: dict[str, object] | None = None,
    ) -> dict[str, object]:
        """Issue a GET request and return the parsed JSON body.

        Retries on 429 and 5xx up to ``http_max_retries`` times with
        exponential back-off.  Non-retryable HTTP errors raise immediately.
        """

        @retry(
            retry=retry_if_exception_type((YelpRateLimitError, YelpServerError)),
            stop=stop_after_attempt(self._max_retries + 1),
            wait=wait_exponential(
                multiplier=1,
                min=self._wait_min,
                max=self._wait_max,
            ),
            before_sleep=_before_sleep,
            reraise=True,
        )
        async def _execute() -> dict[str, object]:
            url = f"{self._base_url}/{path.lstrip('/')}"
            logger.debug("yelp_request", method="GET", url=url, params=params)

            async with httpx.AsyncClient(
                headers=self._headers,
                timeout=self._timeout,
            ) as client:
                resp = await client.get(url, params=params)  # type: ignore[arg-type]

            logger.debug(
                "yelp_response",
                url=url,
                status=resp.status_code,
            )
            return _raise_for_status(resp)

        return await _execute()


def _raise_for_status(resp: httpx.Response) -> dict[str, object]:
    """Convert non-2xx responses to typed YelpAPIError subclasses."""
    if resp.is_success:
        result: dict[str, object] = resp.json()
        return result

    body: dict[str, object] = {}
    try:
        body = resp.json()
    except Exception:
        pass

    error_val = body.get("error") or body.get("description") or resp.text
    message = str(error_val)
    sc = resp.status_code

    if sc == 400:
        raise YelpValidationError(message, sc)
    if sc in (401, 403):
        raise YelpAuthError(message, sc)
    if sc == 404:
        raise YelpNotFoundError(message, sc)
    if sc == 429:
        raise YelpRateLimitError(message, sc)
    if sc >= 500:
        raise YelpServerError(message, sc)

    raise YelpAPIError(message, sc)
