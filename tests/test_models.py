"""Tests for Pydantic output models."""

from __future__ import annotations

from server.core.models import (
    BusinessDetail,
    BusinessReviewsResult,
    BusinessSearchResult,
    BusinessSummary,
    Location,
)


def test_business_summary_minimal() -> None:
    b = BusinessSummary.model_validate({"id": "x", "name": "Y"})
    assert b.id == "x"
    assert b.rating is None
    assert b.categories == []


def test_business_summary_ignores_extra_fields() -> None:
    b = BusinessSummary.model_validate(
        {"id": "x", "name": "Y", "unknown_field_xyz": True}
    )
    assert b.id == "x"


def test_location_display_address() -> None:
    loc = Location.model_validate(
        {"city": "SF", "display_address": ["600 Guerrero St", "San Francisco, CA"]}
    )
    assert len(loc.display_address) == 2


def test_business_search_result_empty() -> None:
    r = BusinessSearchResult.model_validate({"businesses": [], "total": 0})
    assert r.total == 0
    assert r.businesses == []


def test_business_search_result_with_businesses() -> None:
    payload = {
        "businesses": [
            {"id": "a", "name": "Cafe A", "rating": 4.0},
            {"id": "b", "name": "Cafe B", "rating": 3.5},
        ],
        "total": 2,
    }
    r = BusinessSearchResult.model_validate(payload)
    assert len(r.businesses) == 2
    assert r.businesses[0].rating == 4.0


def test_business_detail_with_hours() -> None:
    payload = {
        "id": "d",
        "name": "Dinner Club",
        "hours": [{"hours_type": "REGULAR", "is_open_now": True}],
        "photos": ["http://x.com/1.jpg"],
    }
    d = BusinessDetail.model_validate(payload)
    assert d.hours[0].is_open_now is True
    assert len(d.photos) == 1


def test_business_reviews_result() -> None:
    payload = {
        "reviews": [
            {
                "id": "r1",
                "text": "Great place!",
                "rating": 5,
                "user": {"id": "u1", "name": "Bob"},
            }
        ],
        "total": 1,
        "possible_languages": ["en"],
    }
    r = BusinessReviewsResult.model_validate(payload)
    assert r.total == 1
    assert r.reviews[0].rating == 5
    assert r.reviews[0].user is not None
    assert r.reviews[0].user.name == "Bob"
