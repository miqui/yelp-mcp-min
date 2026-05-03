"""Shared pytest fixtures for yelp-mcp-min tests."""

from __future__ import annotations

import pytest
import respx

import server.core.config as cfg_mod
from server.core.client import YelpClient
from server.core.config import Settings


@pytest.fixture
def settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    """Settings with a fake API key, bypassing env-var requirement."""
    monkeypatch.setenv("YELP_API_KEY", "test-key-abc123")
    # Reset the module-level singleton between tests
    cfg_mod._settings = None
    return cfg_mod.get_settings()


@pytest.fixture
def client(settings: Settings) -> YelpClient:
    """A YelpClient wired to the test settings."""
    return YelpClient(settings)


@pytest.fixture
def mock_yelp(settings: Settings) -> respx.MockRouter:
    """A respx router that intercepts all calls to the Yelp API base URL."""
    with respx.mock(base_url=settings.yelp_base_url, assert_all_called=False) as router:
        yield router
