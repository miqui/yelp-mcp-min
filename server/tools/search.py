"""
Tool: search_businesses

Wraps GET /v3/businesses/search — full-text + filter search across Yelp's
business index with pagination support.
"""

from __future__ import annotations

import structlog
from fastmcp import FastMCP
from pydantic import BaseModel, Field

from server.core.client import YelpClient
from server.core.models import BusinessSearchResult

logger = structlog.get_logger(__name__)


class SearchParams(BaseModel):
    """Parameters for search_businesses."""

    term: str | None = Field(
        default=None,
        description=(
            "Search term, e.g. 'tacos', 'coffee', 'plumbers'. "
            "Omit to browse by location only."
        ),
    )
    location: str | None = Field(
        default=None,
        description=(
            "Address, neighbourhood, city, or ZIP code. "
            "Required unless latitude + longitude are provided."
        ),
    )
    latitude: float | None = Field(
        default=None,
        ge=-90.0,
        le=90.0,
        description="Decimal latitude. Pair with longitude.",
    )
    longitude: float | None = Field(
        default=None,
        ge=-180.0,
        le=180.0,
        description="Decimal longitude. Pair with latitude.",
    )
    radius: int | None = Field(
        default=None,
        ge=1,
        le=40000,
        description="Search radius in metres (max 40 000 ≈ 25 miles).",
    )
    categories: str | None = Field(
        default=None,
        description=(
            "Comma-separated Yelp category aliases, e.g. 'restaurants,bars'. "
            "See https://docs.developer.yelp.com/docs/resources-categories."
        ),
    )
    price: str | None = Field(
        default=None,
        description=(
            "Comma-separated price tiers: '1' = $, '2' = $$, '3' = $$$, '4' = $$$$. "
            "Example: '1,2' returns cheap and moderate results."
        ),
    )
    open_now: bool | None = Field(
        default=None,
        description="When True, only return businesses open at the time of the request.",
    )
    sort_by: str | None = Field(
        default=None,
        description=(
            "Sort order: 'best_match' (default), 'rating', 'review_count', "
            "or 'distance'."
        ),
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=50,
        description="Number of results per page (1–50, default 20).",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description=(
            "Zero-based offset into the full result set. "
            "Use with limit to paginate: page 2 = offset 20 when limit=20."
        ),
    )


def register(mcp: FastMCP, client: YelpClient) -> None:
    """Register the search_businesses tool on the FastMCP instance."""

    @mcp.tool(
        annotations={
            "readOnlyHint": True,
            "openWorldHint": True,
        }
    )
    async def search_businesses(params: SearchParams) -> BusinessSearchResult:
        """Search Yelp for businesses matching a term, location, or both.

        Use this tool when the user wants to discover businesses — restaurants,
        services, shops, entertainment — in a given area. It supports free-text
        search, geo coordinates, category filters, price tiers, open-now
        filtering, and pagination.

        Supply at least one of: location, or both latitude + longitude.

        Returns a list of matching businesses with ratings, review counts, price
        tier, address, and a Yelp URL. The 'total' field indicates how many
        results exist in the full result set; use 'offset' to paginate.

        Raises ValueError when neither location nor coordinates are provided.
        """
        if not params.location and not (params.latitude and params.longitude):
            raise ValueError(
                "Provide 'location' or both 'latitude' and 'longitude'."
            )

        query: dict[str, object] = {}
        for field, value in params.model_dump(exclude_none=True).items():
            query[field] = value

        logger.info("search_businesses", term=params.term, location=params.location)
        raw = await client.get("businesses/search", params=query)
        return BusinessSearchResult.model_validate(raw)
