"""
Yelp MCP server entry point.

Run with:
    uv run python -m server.main

Or via the installed script:
    yelp-mcp
"""

from __future__ import annotations

from fastmcp import FastMCP

from server.core.client import YelpClient
from server.core.config import get_settings
from server.core.logging import configure_logging
from server.resources import business as business_resource
from server.tools import business as business_tools
from server.tools import reviews as reviews_tools
from server.tools import search as search_tools

mcp: FastMCP = FastMCP(
    name="yelp-mcp",
    instructions=(
        "You are connected to the Yelp Fusion API. "
        "Use search_businesses to discover businesses by keyword and location. "
        "Use find_business_by_phone when you have a phone number. "
        "Use match_business when you have a structured name + address. "
        "Use get_business for full details (hours, photos) by Yelp ID or alias. "
        "Use get_business_reviews to read customer reviews. "
        "The yelp://business/{id} resource returns the same data as get_business "
        "and can be embedded directly by MCP clients that support resources."
    ),
)


def _build_server() -> FastMCP:
    settings = get_settings()
    configure_logging(level=settings.log_level, json=settings.json_logs)

    client = YelpClient(settings)

    search_tools.register(mcp, client)
    business_tools.register(mcp, client)
    reviews_tools.register(mcp, client)
    business_resource.register(mcp, client)

    return mcp


def main() -> None:
    server = _build_server()
    server.run()


if __name__ == "__main__":
    main()
