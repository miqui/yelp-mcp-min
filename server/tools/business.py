"""
Tools: find_business_by_phone, match_business, get_business

Wraps:
  GET /v3/businesses/search/phone  → find_business_by_phone
  GET /v3/businesses/matches       → match_business
  GET /v3/businesses/{id}          → get_business
"""

from __future__ import annotations

import structlog
from fastmcp import FastMCP
from pydantic import BaseModel, Field

from server.core.client import YelpClient
from server.core.models import BusinessDetail, BusinessSummary

logger = structlog.get_logger(__name__)


# ── find_business_by_phone ────────────────────────────────────────────────────

class PhoneSearchParams(BaseModel):
    phone: str = Field(
        ...,
        description=(
            "Phone number in E.164 format including country code, e.g. '+14155551234'. "
            "Leading '+' and country code are required."
        ),
    )


# ── match_business ────────────────────────────────────────────────────────────

class MatchParams(BaseModel):
    name: str = Field(..., description="Business name, e.g. 'Tartine Bakery'.")
    address1: str = Field(..., description="Street address, e.g. '600 Guerrero St'.")
    city: str = Field(..., description="City name, e.g. 'San Francisco'.")
    state: str = Field(
        ...,
        description="ISO 3166-2 state/region code, e.g. 'CA' for California.",
    )
    country: str = Field(
        ...,
        description="ISO 3166-1 alpha-2 country code, e.g. 'US'.",
    )
    zip_code: str | None = Field(
        default=None,
        description="Postal code, e.g. '94110'. Improves match accuracy.",
    )
    phone: str | None = Field(
        default=None,
        description="E.164 phone number. Improves match accuracy.",
    )
    match_threshold: str = Field(
        default="DEFAULT",
        description=(
            "Strictness of the name/address match: 'NONE', 'DEFAULT', or 'STRICT'. "
            "Use 'STRICT' to minimise false positives."
        ),
    )


# ── get_business ──────────────────────────────────────────────────────────────

class GetBusinessParams(BaseModel):
    business_id: str = Field(
        ...,
        description=(
            "Yelp business ID or alias, e.g. 'tartine-bakery-san-francisco'. "
            "Obtain from search_businesses, find_business_by_phone, or match_business."
        ),
    )
    locale: str | None = Field(
        default=None,
        description=(
            "BCP 47 locale for response localisation, e.g. 'en_US', 'fr_FR'. "
            "Defaults to en_US."
        ),
    )


def register(mcp: FastMCP, client: YelpClient) -> None:
    """Register business lookup tools on the FastMCP instance."""

    @mcp.tool(
        annotations={
            "readOnlyHint": True,
            "idempotentHint": True,
        }
    )
    async def find_business_by_phone(params: PhoneSearchParams) -> list[BusinessSummary]:
        """Look up Yelp businesses that match a phone number.

        Use this when you have a phone number and need to identify which
        business it belongs to.  Returns up to a handful of candidates ranked
        by relevance.  An empty list means no Yelp listing was found for that
        number.

        The phone must include the country code in E.164 format (+14155551234).
        """
        logger.info("find_business_by_phone", phone=params.phone)
        raw = await client.get(
            "businesses/search/phone",
            params={"phone": params.phone},
        )
        businesses: list[object] = raw.get("businesses", [])  # type: ignore[assignment]
        return [BusinessSummary.model_validate(b) for b in businesses]

    @mcp.tool(
        annotations={
            "readOnlyHint": True,
            "idempotentHint": True,
        }
    )
    async def match_business(params: MatchParams) -> list[BusinessDetail]:
        """Match a business by name and address to its canonical Yelp listing.

        Use this when you have structured address data (from a CRM, spreadsheet,
        or user input) and need to verify or enrich it with Yelp data such as
        the Yelp ID, rating, hours, and URL.

        Name + address1 + city + state + country are required.  Adding zip_code
        and phone significantly improves match precision.

        Returns ranked candidates; the first result is the best match.
        An empty list means no match was found at the chosen threshold.
        """
        query: dict[str, object] = params.model_dump(exclude_none=True)
        logger.info("match_business", name=params.name, city=params.city)
        raw = await client.get("businesses/matches", params=query)
        businesses: list[object] = raw.get("businesses", [])  # type: ignore[assignment]
        return [BusinessDetail.model_validate(b) for b in businesses]

    @mcp.tool(
        annotations={
            "readOnlyHint": True,
            "idempotentHint": True,
        }
    )
    async def get_business(params: GetBusinessParams) -> BusinessDetail:
        """Fetch the full Yelp profile for a specific business by its ID or alias.

        Use this when you already have a Yelp business ID (from search results
        or a previous call) and need complete details: hours, all photos, full
        address, price tier, categories, and the Yelp URL.

        Raises an error if the business ID does not exist on Yelp.
        """
        logger.info("get_business", business_id=params.business_id)
        query: dict[str, object] = {}
        if params.locale:
            query["locale"] = params.locale
        raw = await client.get(
            f"businesses/{params.business_id}",
            params=query or None,
        )
        return BusinessDetail.model_validate(raw)
