from pydantic import BaseModel, Field, field_validator, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from bson import ObjectId
from pydantic_core import core_schema


class PyObjectId(str):
    """Custom ObjectId for Pydantic models that serializes as string"""
    
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        return core_schema.with_info_after_validator_function(
            lambda v, info: str(v) if v else None,
            core_schema.any_schema(),
            serialization=core_schema.str_schema(),
        )
    
    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        return {"type": "string", "format": "objectid"}


class ChainCategory(str, Enum):
    LUXURY = "Luxury"
    UPPER_UPSCALE = "Upper Upscale"
    UPSCALE = "Upscale"
    UPPER_MIDSCALE = "Upper Midscale"
    MIDSCALE = "Midscale"
    ECONOMY = "Economy"
    BUDGET = "Budget"


class QualityRating(str, Enum):
    LUXURY = "Luxury"
    UPSCALE = "Upscale"
    MIDSCALE = "Midscale"
    ECONOMY = "Economy"
    BUDGET = "Budget"


class PropertyType(str, Enum):
    HOTEL = "Hotel"
    RESORT = "Resort"
    MOTEL = "Motel"
    APARTHOTEL = "Aparthotel"
    HOSTEL = "Hostel"
    BED_AND_BREAKFAST = "Bed and Breakfast"
    VILLA = "Villa"
    SERVICED_APARTMENT = "Serviced Apartment"


class ApartmentType(str, Enum):
    SERVICED_APARTMENT = "Serviced Apartment"
    STUDIO = "Studio"
    ONE_BEDROOM = "One Bedroom"
    TWO_BEDROOM = "Two Bedroom"
    THREE_BEDROOM = "Three Bedroom"
    PENTHOUSE = "Penthouse"


class LocationType(str, Enum):
    URBAN = "Urban"
    SUBURBAN = "Suburban"
    RESORT = "Resort"
    AIRPORT = "Airport"
    BEACH = "Beach"
    MOUNTAIN = "Mountain"
    RURAL = "Rural"


class BuildingClass(str, Enum):
    LUXURY = "Luxury"
    UPPER_UPSCALE = "Upper Upscale"
    UPSCALE = "Upscale"
    MIDSCALE = "Midscale"
    ECONOMY = "Economy"


class ScrapeStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    PARTIAL = "partial"


class Brand(BaseModel):
    name: str = Field(..., description="Brand name")
    chain_category: Optional[ChainCategory] = Field(
        default=None,
        alias="chainCategory",
        description="Hotel chain category"
    )


class Contact(BaseModel):
    phone: Optional[str] = Field(default=None, description="Contact phone number")
    email: Optional[str] = Field(default=None, description="Contact email address")
    website: Optional[HttpUrl] = Field(default=None, description="Hotel website URL")
    booking_url: Optional[HttpUrl] = Field(
        default=None,
        alias="bookingUrl",
        description="Direct booking URL"
    )


class GuestRating(BaseModel):
    score: Optional[float] = Field(default=None, ge=0, le=10, description="Guest rating score")
    source: Optional[str] = Field(default=None, description="Rating source (e.g., Booking.com, TripAdvisor)")
    last_scraped: Optional[datetime] = Field(
        default=None,
        alias="lastScraped",
        description="Last time rating was scraped"
    )


class Rating(BaseModel):
    stars: Optional[float] = Field(default=None, ge=0, le=5, description="Star rating")
    quality: Optional[QualityRating] = Field(default=None, description="Quality category")
    guest: Optional[GuestRating] = Field(default=None, description="Guest ratings")


class Address(BaseModel):
    building_name: Optional[str] = Field(
        default=None,
        alias="buildingName",
        description="Building name"
    )
    street: str = Field(..., description="Street address")
    city: str = Field(..., description="City")
    state: Optional[str] = Field(default=None, description="State or province")
    zip: Optional[str] = Field(default=None, description="Postal/ZIP code")
    country: str = Field(..., description="Country")


class Coordinates(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lng: float = Field(..., ge=-180, le=180, description="Longitude")


class Distances(BaseModel):
    beach_km: Optional[float] = Field(
        default=None,
        alias="beach_km",
        ge=0,
        description="Distance to beach in kilometers"
    )
    cbd_km: Optional[float] = Field(
        default=None,
        alias="cbd_km",
        ge=0,
        description="Distance to CBD in kilometers"
    )
    transport_km: Optional[float] = Field(
        default=None,
        alias="transport_km",
        ge=0,
        description="Distance to nearest transport in kilometers"
    )


class Location(BaseModel):
    address: Address = Field(..., description="Physical address")
    coordinates: Coordinates = Field(..., description="GPS coordinates")
    distances: Optional[Distances] = Field(default=None, description="Distances to key locations")
    nearby_transport: Optional[List[str]] = Field(
        default_factory=list,
        alias="nearbyTransport",
        description="Available nearby transport options"
    )
    type: Optional[LocationType] = Field(default=None, description="Location type")


class MeetingFacilities(BaseModel):
    room_count: Optional[int] = Field(
        default=None,
        alias="roomCount",
        ge=0,
        description="Number of meeting rooms"
    )
    capacity: Optional[int] = Field(
        default=None,
        ge=0,
        description="Maximum meeting capacity"
    )
    max_contiguous_space: Optional[str] = Field(
        default=None,
        alias="maxContiguousSpace",
        description="Maximum contiguous space available"
    )


class Property(BaseModel):
    type: Optional[PropertyType] = Field(default=None, description="Property type")
    apartment_type: Optional[ApartmentType] = Field(
        default=None,
        alias="apartmentType",
        description="Apartment type if applicable"
    )
    floors: Optional[int] = Field(default=None, ge=0, description="Number of floors")
    rooms: Optional[int] = Field(default=None, ge=0, description="Number of rooms")
    meeting: Optional[MeetingFacilities] = Field(
        default=None,
        description="Meeting facilities details"
    )
    building_class: Optional[BuildingClass] = Field(
        default=None,
        alias="buildingClass",
        description="Building class rating"
    )
    market: Optional[str] = Field(default=None, description="Market area")
    submarket: Optional[str] = Field(default=None, description="Submarket area")
    year_built: Optional[int] = Field(
        default=None,
        alias="yearBuilt",
        ge=1800,
        le=2100,
        description="Year the property was built"
    )
    last_renovated: Optional[int] = Field(
        default=None,
        alias="lastRenovated",
        ge=1800,
        le=2100,
        description="Year of last renovation"
    )


class Amenities(BaseModel):
    facilities: List[str] = Field(
        default_factory=list,
        description="List of facilities available"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="User-generated tags"
    )
    ai_tags: List[str] = Field(
        default_factory=list,
        alias="aiTags",
        description="AI-generated tags"
    )


class AI(BaseModel):
    summary: Optional[str] = Field(default=None, description="AI-generated summary")
    confidence_score: Optional[float] = Field(
        default=None,
        alias="confidenceScore",
        ge=0,
        le=1,
        description="Confidence score for AI data"
    )


class Scrape(BaseModel):
    source: Optional[HttpUrl] = Field(default=None, description="Source URL of scraped data")
    status: ScrapeStatus = Field(..., description="Scraping status")
    last_scraped: Optional[datetime] = Field(
        default=None,
        alias="lastScraped",
        description="Last scrape timestamp"
    )


class RecommendationPriority(BaseModel):
    score: Optional[float] = Field(
        default=None,
        ge=0,
        le=10,
        description="Recommendation priority score"
    )
    reason: Optional[str] = Field(default=None, description="Reason for priority score")
    updated_at: Optional[datetime] = Field(
        default=None,
        alias="updatedAt",
        description="Last updated timestamp"
    )


class Hotel(BaseModel):
    id: Optional[PyObjectId] = Field(
        default_factory=lambda: PyObjectId(str(ObjectId())),
        alias="_id"
    )
    name: str = Field(..., min_length=1, description="Hotel name")
    description: Optional[str] = Field(default=None, description="Hotel description")
    brand: Optional[Brand] = Field(default=None, description="Brand information")
    contact: Optional[Contact] = Field(default=None, description="Contact information")
    rating: Optional[Rating] = Field(default=None, description="Rating information")
    location: Location = Field(..., description="Location details")
    property: Optional[Property] = Field(default=None, description="Property details")
    amenities: Optional[Amenities] = Field(default=None, description="Amenities information")
    ai: Optional[AI] = Field(default=None, description="AI-generated information")
    scrape: Optional[Scrape] = Field(default=None, description="Scraping metadata")
    images: List[str] = Field(default_factory=list, description="Image URLs")
    recommendation_priority: Optional[RecommendationPriority] = Field(
        default=None,
        alias="recommendation_priority",
        description="Recommendation priority data"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "validate_assignment": True
    }
    
    @field_validator('id', mode='before')
    @classmethod
    def validate_object_id(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            return PyObjectId(v)
        if isinstance(v, ObjectId):
            return PyObjectId(str(v))
        return v


class HotelCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    brand: Optional[Brand] = None
    contact: Optional[Contact] = None
    rating: Optional[Rating] = None
    location: Location
    property: Optional[Property] = None
    amenities: Optional[Amenities] = None
    ai: Optional[AI] = None
    scrape: Optional[Scrape] = None
    images: List[str] = Field(default_factory=list)
    recommendation_priority: Optional[RecommendationPriority] = None


class HotelUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = None
    brand: Optional[Brand] = None
    contact: Optional[Contact] = None
    rating: Optional[Rating] = None
    location: Optional[Location] = None
    property: Optional[Property] = None
    amenities: Optional[Amenities] = None
    ai: Optional[AI] = None
    scrape: Optional[Scrape] = None
    images: Optional[List[str]] = None
    recommendation_priority: Optional[RecommendationPriority] = None


class HotelResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    brand: Optional[Brand] = None
    contact: Optional[Contact] = None
    rating: Optional[Rating] = None
    location: Location
    property: Optional[Property] = None
    amenities: Optional[Amenities] = None
    ai: Optional[AI] = None
    scrape: Optional[Scrape] = None
    images: List[str] = Field(default_factory=list)
    recommendation_priority: Optional[RecommendationPriority] = None
    created_at: datetime
    updated_at: datetime


class HotelListResponse(BaseModel):
    hotels: List[HotelResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

