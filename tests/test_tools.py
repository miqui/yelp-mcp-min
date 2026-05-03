"""Tests for MCP tools (search, business, reviews)."""

from __future__ import annotations

import httpx
import pydantic
import pytest
import respx

from server.core.client import YelpClient, YelpNotFoundError
from server.core.models import BusinessDetail, BusinessReviewsResult, BusinessSearchResult
from server.tools.business import MatchParams, PhoneSearchParams
from server.tools.reviews import ReviewsParams
from server.tools.search import SearchParams

# ── Fixtures ──────────────────────────────────────────────────────────────────

BUSINESS_SUMMARY = {
    "id": "abc-123",
    "name": "Tartine Bakery",
    "rating": 4.5,
    "review_count": 3000,
    "location": {"address1": "600 Guerrero St", "city": "San Francisco"},
    "is_closed": False,
}

BUSINESS_DETAIL = {
    **BUSINESS_SUMMARY,
    "photos": [],
    "hours": [],
    "alias": "tartine-bakery-san-francisco",
}

REVIEW = {
    "id": "rev-1",
    "text": "Amazing croissants!",
    "rating": 5,
    "time_created": "2024-01-01 10:00:00",
    "user": {"id": "usr-1", "name": "Alice"},
}


# ── search_businesses ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_search_businesses_returns_results(
    client: YelpClient, mock_yelp: respx.MockRouter
) -> None:
    mock_yelp.get("/businesses/search").mock(
        return_value=httpx.Response(
            200,
            json={"businesses": [BUSINESS_SUMMARY], "total": 1},
        )
    )
    params = SearchParams(term="bakery", location="San Francisco", limit=20, offset=0)
    query: dict[str, object] = {k: v for k, v in params.model_dump(exclude_none=True).items()}
    raw = await client.get("businesses/search", params=query)
    result = BusinessSearchResult.model_validate(raw)

    assert result.total == 1
    assert result.businesses[0].name == "Tartine Bakery"


@pytest.mark.asyncio
async def test_search_businesses_pagination(
    client: YelpClient, mock_yelp: respx.MockRouter
) -> None:
    mock_yelp.get("/businesses/search").mock(
        return_value=httpx.Response(200, json={"businesses": [], "total": 100})
    )
    params = SearchParams(location="NYC", limit=10, offset=20)
    assert params.limit == 10
    assert params.offset == 20


def test_search_params_location_optional_in_model() -> None:
    """The pydantic model doesn't require location; the tool function does."""
    params = SearchParams(term="coffee")
    assert params.location is None
    assert params.latitude is None


def test_search_params_limit_bounds() -> None:
    with pytest.raises(pydantic.ValidationError):
        SearchParams(location="NYC", limit=0)
    with pytest.raises(pydantic.ValidationError):
        SearchParams(location="NYC", limit=51)


# ── find_business_by_phone ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_find_by_phone_returns_list(
    client: YelpClient, mock_yelp: respx.MockRouter
) -> None:
    mock_yelp.get("/businesses/search/phone").mock(
        return_value=httpx.Response(200, json={"businesses": [BUSINESS_SUMMARY]})
    )
    raw = await client.get("businesses/search/phone", params={"phone": "+14155551234"})
    businesses = raw.get("businesses", [])
    assert len(businesses) == 1  # type: ignore[arg-type]


def test_phone_search_params_required() -> None:
    with pytest.raises(pydantic.ValidationError):
        PhoneSearchParams()  # type: ignore[call-arg]


# ── match_business ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_match_business_returns_list(
    client: YelpClient, mock_yelp: respx.MockRouter
) -> None:
    mock_yelp.get("/businesses/matches").mock(
        return_value=httpx.Response(200, json={"businesses": [BUSINESS_DETAIL]})
    )
    raw = await client.get(
        "businesses/matches",
        params={
            "name": "Tartine Bakery",
            "address1": "600 Guerrero St",
            "city": "San Francisco",
            "state": "CA",
            "country": "US",
        },
    )
    assert len(raw.get("businesses", [])) == 1  # type: ignore[arg-type]


def test_match_params_required_fields() -> None:
    with pytest.raises(pydantic.ValidationError):
        MatchParams(name="X")  # type: ignore[call-arg]


# ── get_business ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_business_returns_detail(
    client: YelpClient, mock_yelp: respx.MockRouter
) -> None:
    mock_yelp.get("/businesses/tartine-bakery-san-francisco").mock(
        return_value=httpx.Response(200, json=BUSINESS_DETAIL)
    )
    raw = await client.get("businesses/tartine-bakery-san-francisco")
    detail = BusinessDetail.model_validate(raw)
    assert detail.id == "abc-123"
    assert detail.alias == "tartine-bakery-san-francisco"


@pytest.mark.asyncio
async def test_get_business_not_found(
    client: YelpClient, mock_yelp: respx.MockRouter
) -> None:
    mock_yelp.get("/businesses/does-not-exist").mock(
        return_value=httpx.Response(404, json={"error": "not found"})
    )
    with pytest.raises(YelpNotFoundError):
        await client.get("businesses/does-not-exist")


# ── get_business_reviews ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_reviews_returns_result(
    client: YelpClient, mock_yelp: respx.MockRouter
) -> None:
    mock_yelp.get("/businesses/abc-123/reviews").mock(
        return_value=httpx.Response(
            200,
            json={"reviews": [REVIEW], "total": 1, "possible_languages": ["en"]},
        )
    )
    raw = await client.get(
        "businesses/abc-123/reviews",
        params={"limit": 20, "offset": 0},
    )
    result = BusinessReviewsResult.model_validate(raw)
    assert result.total == 1
    assert result.reviews[0].text == "Amazing croissants!"


def test_reviews_params_limit_bounds() -> None:
    with pytest.raises(pydantic.ValidationError):
        ReviewsParams(business_id="x", limit=0)
    with pytest.raises(pydantic.ValidationError):
        ReviewsParams(business_id="x", limit=51)


def test_reviews_params_offset_nonnegative() -> None:
    with pytest.raises(pydantic.ValidationError):
        ReviewsParams(business_id="x", offset=-1)
