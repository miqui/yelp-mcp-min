"""
Tool: get_business_reviews

Wraps GET /v3/businesses/{id}/reviews
"""

from __future__ import annotations

import structlog
from fastmcp import FastMCP
from pydantic import BaseModel, Field

from server.core.client import YelpClient
from server.core.models import BusinessReviewsResult

logger = structlog.get_logger(__name__)


class ReviewsParams(BaseModel):
    business_id: str = Field(
        ...,
        description=(
            "Yelp business ID or alias. "
            "Obtain from search_businesses, find_business_by_phone, or match_business."
        ),
    )
    locale: str | None = Field(
        default=None,
        description=(
            "BCP 47 locale to filter reviews by language, e.g. 'en_US', 'es_MX'. "
            "Defaults to all languages."
        ),
    )
    sort_by: str | None = Field(
        default=None,
        description=(
            "Sort order for reviews: 'yelp_sort' (default), 'newest', 'oldest', "
            "'highest_rated', or 'lowest_rated'."
        ),
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=50,
        description="Number of reviews to return (1–50, default 20).",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description=(
            "Zero-based offset for pagination. "
            "Use with limit to page through all reviews."
        ),
    )


def register(mcp: FastMCP, client: YelpClient) -> None:
    """Register the get_business_reviews tool on the FastMCP instance."""

    @mcp.tool(
        annotations={
            "readOnlyHint": True,
            "idempotentHint": True,
        }
    )
    async def get_business_reviews(params: ReviewsParams) -> BusinessReviewsResult:
        """Retrieve user reviews for a specific Yelp business.

        Use this when the user wants to read what customers say about a
        business: sentiment, specific comments about food, service, or
        atmosphere.  Returns up to 50 reviews per call with text excerpts,
        star ratings, and reviewer info.

        The 'total' field in the response shows how many reviews exist in full;
        use 'offset' to paginate through them.

        Raises an error if the business ID does not exist on Yelp.
        """
        query: dict[str, object] = {
            "limit": params.limit,
            "offset": params.offset,
        }
        if params.locale:
            query["locale"] = params.locale
        if params.sort_by:
            query["sort_by"] = params.sort_by

        logger.info("get_business_reviews", business_id=params.business_id)
        raw = await client.get(
            f"businesses/{params.business_id}/reviews",
            params=query,
        )
        return BusinessReviewsResult.model_validate(raw)
