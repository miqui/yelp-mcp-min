"""Tests for the YelpClient HTTP layer."""

from __future__ import annotations

import httpx
import pytest
import respx

from server.core.client import (
    YelpAuthError,
    YelpClient,
    YelpNotFoundError,
    YelpRateLimitError,
    YelpServerError,
    YelpValidationError,
)
from server.core.config import Settings


@pytest.fixture
def client(settings: Settings) -> YelpClient:
    return YelpClient(settings)


@pytest.mark.asyncio
async def test_get_success(client: YelpClient, mock_yelp: respx.MockRouter) -> None:
    mock_yelp.get("/businesses/search").mock(
        return_value=httpx.Response(200, json={"businesses": [], "total": 0})
    )
    result = await client.get("businesses/search", params={"location": "SF"})
    assert result["total"] == 0


@pytest.mark.asyncio
async def test_get_404_raises_not_found(
    client: YelpClient, mock_yelp: respx.MockRouter
) -> None:
    mock_yelp.get("/businesses/bad-id").mock(
        return_value=httpx.Response(404, json={"error": {"description": "not found"}})
    )
    with pytest.raises(YelpNotFoundError):
        await client.get("businesses/bad-id")


@pytest.mark.asyncio
async def test_get_401_raises_auth_error(
    client: YelpClient, mock_yelp: respx.MockRouter
) -> None:
    mock_yelp.get("/businesses/x").mock(
        return_value=httpx.Response(401, json={"error": "Unauthorized"})
    )
    with pytest.raises(YelpAuthError):
        await client.get("businesses/x")


@pytest.mark.asyncio
async def test_get_400_raises_validation_error(
    client: YelpClient, mock_yelp: respx.MockRouter
) -> None:
    mock_yelp.get("/businesses/search").mock(
        return_value=httpx.Response(400, json={"error": "VALIDATION_ERROR"})
    )
    with pytest.raises(YelpValidationError):
        await client.get("businesses/search")


@pytest.mark.asyncio
async def test_get_429_raises_rate_limit(
    client: YelpClient, settings: Settings, mock_yelp: respx.MockRouter
) -> None:
    # Disable retries for this test so it doesn't actually wait
    settings.http_max_retries = 0
    mock_yelp.get("/businesses/search").mock(
        return_value=httpx.Response(429, json={"error": "RATE_LIMIT_ERROR"})
    )
    with pytest.raises(YelpRateLimitError):
        await client.get("businesses/search")


@pytest.mark.asyncio
async def test_get_500_raises_server_error(
    client: YelpClient, settings: Settings, mock_yelp: respx.MockRouter
) -> None:
    settings.http_max_retries = 0
    mock_yelp.get("/businesses/search").mock(
        return_value=httpx.Response(500, json={"error": "INTERNAL_ERROR"})
    )
    with pytest.raises(YelpServerError):
        await client.get("businesses/search")


@pytest.mark.asyncio
async def test_auth_header_sent(
    client: YelpClient, mock_yelp: respx.MockRouter
) -> None:
    route = mock_yelp.get("/businesses/test").mock(
        return_value=httpx.Response(200, json={"id": "test"})
    )
    await client.get("businesses/test")
    request = route.calls.last.request
    assert request.headers["authorization"] == "Bearer test-key-abc123"
