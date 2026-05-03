"""
Pydantic output models for Yelp Fusion API responses.

These models define the shapes returned by tools and resources.
Only fields that are consistently present in the API response are declared;
extras are silently ignored via model_config.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class _YelpBase(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)


# ── Shared sub-models ─────────────────────────────────────────────────────────

class Location(BaseModel):
    model_config = ConfigDict(extra="ignore")

    address1: str | None = None
    address2: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    country: str | None = None
    display_address: list[str] = Field(default_factory=list)


class Category(BaseModel):
    model_config = ConfigDict(extra="ignore")

    alias: str
    title: str


class Coordinates(BaseModel):
    model_config = ConfigDict(extra="ignore")

    latitude: float | None = None
    longitude: float | None = None


class Hours(BaseModel):
    model_config = ConfigDict(extra="ignore")

    hours_type: str | None = None
    is_open_now: bool = False


# ── Business summary (used in search results) ─────────────────────────────────

class BusinessSummary(_YelpBase):
    """Condensed business record returned by search and phone-search tools."""

    id: str
    name: str
    url: str | None = None
    phone: str | None = None
    display_phone: str | None = None
    rating: float | None = None
    review_count: int | None = None
    price: str | None = None
    is_closed: bool = False
    distance: float | None = None
    location: Location | None = None
    categories: list[Category] = Field(default_factory=list)
    coordinates: Coordinates | None = None
    image_url: str | None = None


# ── Full business detail ──────────────────────────────────────────────────────

class BusinessDetail(_YelpBase):
    """Full business record returned by get_business and match_business."""

    id: str
    name: str
    url: str | None = None
    phone: str | None = None
    display_phone: str | None = None
    rating: float | None = None
    review_count: int | None = None
    price: str | None = None
    is_closed: bool = False
    location: Location | None = None
    categories: list[Category] = Field(default_factory=list)
    coordinates: Coordinates | None = None
    image_url: str | None = None
    photos: list[str] = Field(default_factory=list)
    hours: list[Hours] = Field(default_factory=list)
    alias: str | None = None


# ── Search response wrapper ───────────────────────────────────────────────────

class BusinessSearchResult(_YelpBase):
    """Wrapper returned by search_businesses."""

    businesses: list[BusinessSummary] = Field(default_factory=list)
    total: int = 0
    region: dict[str, object] | None = None


# ── Reviews ───────────────────────────────────────────────────────────────────

class ReviewUser(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str | None = None
    profile_url: str | None = None
    image_url: str | None = None
    name: str | None = None


class Review(_YelpBase):
    id: str
    url: str | None = None
    text: str | None = None
    rating: int | None = None
    time_created: str | None = None
    user: ReviewUser | None = None


class BusinessReviewsResult(_YelpBase):
    """Wrapper returned by get_business_reviews."""

    reviews: list[Review] = Field(default_factory=list)
    total: int = 0
    possible_languages: list[str] = Field(default_factory=list)
