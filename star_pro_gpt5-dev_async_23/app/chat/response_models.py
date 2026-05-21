from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class HotelPosition(BaseModel):
    lat: Optional[float] = Field(description="Latitude coordinate")
    lng: Optional[float] = Field(description="Longitude coordinate")


class ExtraPrice(BaseModel):
    source: Optional[str] = Field(description="Booking source name (e.g., 'Booking.com', 'Expedia')")
    source_url: Optional[str] = Field(description="URL to the booking page")
    price: Optional[int] = Field(description="Price per night from this source")


class HotelResult(BaseModel):
    id: Optional[str] = Field(description="Unique identifier for the hotel")
    name: Optional[str] = Field(description="Hotel name")
    link: Optional[str] = Field(description="Hotel link")
    description: Optional[str] = Field(description="Hotel description")
    rating: Optional[float] = Field(description="Average rating (e.g., 4.4)")
    reviews: Optional[int] = Field(description="Number of reviews")
    stars: Optional[int] = Field(description="Star rating (1-5)")
    address: Optional[str] = Field(description="Hotel address")
    phone: Optional[str] = Field(description="Contact phone number")
    features: Optional[List[str]] = Field(description="List of hotel features/amenities")
    price: Optional[str] = Field(description="Price per night (e.g., '$847')")
    priceLabel: Optional[str] = Field(description="Price label (e.g., 'Best Price')")
    roomType: Optional[str] = Field(description="Type of room")
    source: Optional[str] = Field(description="Booking source (e.g., 'Booking.com')")
    sourceUrl: Optional[str] = Field(description="URL to booking source")
    imageUrls: Optional[List[str]] = Field(description="Hotel image URLs")
    aiNote: Optional[str] = Field(description="AI-generated recommendation note")
    position: Optional[HotelPosition] = Field(description="Geographic coordinates")
    extra_prices: Optional[List[ExtraPrice]] = Field(description="Additional booking options with different prices and sources")


class HotelSearchResponse(BaseModel):
    resultsTitle: str = Field(description="Title describing the search criteria and results")
    results: List[HotelResult] = Field(description="List of hotel results")


class WebSearchImage(BaseModel):
    url: str = Field(description="Direct image URL")
    description: Optional[str] = Field(description="AI-generated description of the image content")


class WebSearchResponse(BaseModel):
    resultsTitle: str = Field(description="Title describing the search criteria and results")
    images: List[WebSearchImage] = Field(description="List of relevant images with descriptions")


class StructuredChatResponse(BaseModel):
    """Response model that can contain either a regular message, structured hotel data, or web search images"""
    message: Optional[str] = Field(None, description="Regular chat message")
    hotelSearch: Optional[HotelSearchResponse] = Field(None, description="Structured hotel search results")
    webSearch: Optional[WebSearchResponse] = Field(None, description="Web search images with descriptions")
    session_id: str = Field(..., description="Session ID for conversation continuity")
    tab_id: Optional[str] = Field(None, description="Tab ID for the current chat tab")
    tab_name_suggestion: Optional[str] = Field(None, description="Suggested tab name for new conversations")
    suggestions: Optional[List[str]] = Field(None, description="3 AI-generated suggestions for the user's next message")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional response metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
