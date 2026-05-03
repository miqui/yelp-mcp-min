"""
Resource: yelp://business/{id}

Exposes a full business profile as a JSON resource so MCP clients can
subscribe to or embed business data directly without calling a tool.
"""

from __future__ import annotations

import json

import structlog
from fastmcp import FastMCP

from server.core.client import YelpClient
from server.core.models import BusinessDetail

logger = structlog.get_logger(__name__)


def register(mcp: FastMCP, client: YelpClient) -> None:
    """Register the yelp://business/{id} resource on the FastMCP instance."""

    @mcp.resource(
        "yelp://business/{business_id}",
        mime_type="application/json",
        name="yelp_business",
        description=(
            "Full Yelp business profile for a given business ID or alias. "
            "Returns the same payload as get_business but as an MCP resource "
            "that clients can embed or subscribe to."
        ),
    )
    async def business_resource(business_id: str) -> str:
        """Fetch and serialise a full business profile as a JSON string."""
        logger.info("resource_business", business_id=business_id)
        raw = await client.get(f"businesses/{business_id}")
        detail = BusinessDetail.model_validate(raw)
        return json.dumps(detail.model_dump(exclude_none=True), indent=2)
