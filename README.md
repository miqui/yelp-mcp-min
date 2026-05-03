# yelp-mcp-min

Minimal MCP server for the Yelp Fusion API v3, built with FastMCP 3.

## Prerequisites

- Python 3.11+
- uv 0.11+
- Docker (optional)
- A Yelp Fusion API key — https://www.yelp.com/developers/v3/manage_app

## Installation

```bash
uv sync
cp .env.example .env
# Edit .env and set YELP_API_KEY
```

## Running

```bash
# stdio transport (for use with Claude Desktop or an MCP client)
uv run python -m server.main

# Docker
docker build -t yelp-mcp-min .
docker run --env-file .env yelp-mcp-min
docker buildx build -t yelp-mcp-min .
```

## Environment variables

| Variable             | Required | Default                    | Description                          |
|----------------------|----------|----------------------------|--------------------------------------|
| `YELP_API_KEY`       | Yes      | —                          | Yelp Fusion API bearer token         |
| `YELP_BASE_URL`      | No       | `https://api.yelp.com/v3`  | API base URL                         |
| `HTTP_TIMEOUT`       | No       | `10.0`                     | Request timeout in seconds           |
| `HTTP_MAX_RETRIES`   | No       | `3`                        | Max retry attempts on 429/5xx        |
| `HTTP_RETRY_WAIT_MIN`| No       | `1.0`                      | Min back-off wait in seconds         |
| `HTTP_RETRY_WAIT_MAX`| No       | `10.0`                     | Max back-off wait in seconds         |
| `LOG_LEVEL`          | No       | `INFO`                     | structlog level                      |
| `JSON_LOGS`          | No       | `false`                    | Emit JSON log lines (for Datadog etc)|

## Tools

| Tool                    | Yelp endpoint                        | Description                                    |
|-------------------------|--------------------------------------|------------------------------------------------|
| `search_businesses`     | `GET /v3/businesses/search`          | Full-text + geo search with pagination         |
| `find_business_by_phone`| `GET /v3/businesses/search/phone`    | Look up a business by E.164 phone number       |
| `match_business`        | `GET /v3/businesses/matches`         | Match structured name+address to Yelp listing  |
| `get_business`          | `GET /v3/businesses/{id}`            | Full business profile by Yelp ID or alias      |
| `get_business_reviews`  | `GET /v3/businesses/{id}/reviews`    | Customer reviews with pagination               |

## Resource

`yelp://business/{id}` — Returns the same payload as `get_business` as an MCP
resource (`application/json`). MCP clients that support resources can embed or
subscribe to this URI directly.

## Project structure

```
yelp-mcp-min/
  server/
    main.py              # FastMCP instance + wiring
    core/
      config.py          # pydantic-settings (YELP_API_KEY, tunables)
      logging.py         # structlog setup (stderr only)
      client.py          # async httpx client, retry, error mapping
      models.py          # Pydantic output models
    tools/
      search.py          # search_businesses
      business.py        # find_by_phone, match, get_business
      reviews.py         # get_business_reviews
    resources/
      business.py        # yelp://business/{id}
  tests/
    conftest.py
    test_client.py
    test_tools.py
    test_models.py
  Dockerfile
  pyproject.toml
  .env.example
```

## Running tests

```bash
uv run pytest -v
```
