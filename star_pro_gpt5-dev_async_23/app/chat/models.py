from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from app.models.chat import ChatSession as MongoDBChatSession, ChatTab as MongoDBChatTab


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    role: MessageRole
    content: str
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    tab_id: Optional[str] = Field(None, description="Tab ID for the current chat tab")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the chat")


class ChatResponse(BaseModel):
    message: str = Field(..., description="AI response message")
    session_id: str = Field(..., description="Session ID for conversation continuity")
    tab_id: Optional[str] = Field(None, description="Tab ID for the current chat tab")
    conversation_id: Optional[str] = Field(None, description="Conversation identifier")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional response metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Use the MongoDB ChatSession model instead of duplicating
ChatSession = MongoDBChatSession
ChatTab = MongoDBChatTab


class CreateTabRequest(BaseModel):
    title: Optional[str] = Field(default="New Chat", description="Tab title")
    session_id: Optional[str] = Field(None, description="Existing session ID to associate with")


class UpdateTabRequest(BaseModel):
    title: Optional[str] = Field(None, description="New tab title")
    is_pinned: Optional[bool] = Field(None, description="Whether to pin the tab")
    order_index: Optional[int] = Field(None, description="New order index")


class TabResponse(BaseModel):
    tab_id: str = Field(..., description="Tab identifier")
    title: str = Field(..., description="Tab title")
    session_id: str = Field(..., description="Associated session ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    message_count: int = Field(..., description="Number of messages")
    is_active: bool = Field(..., description="Whether tab is active")
    is_pinned: bool = Field(..., description="Whether tab is pinned")
    order_index: int = Field(..., description="Order index")


class ToolResult(BaseModel):
    tool_name: str
    result: str
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SerpAPIHotelsInput(BaseModel):
    # Required parameters
    query: str = Field(description="Search query - anything you would use in a regular Google Hotels search")
    check_in_date: str = Field(description="Check-in date in YYYY-MM-DD format (e.g., 2025-08-13)")
    check_out_date: str = Field(description="Check-out date in YYYY-MM-DD format (e.g., 2025-08-14)")
    
    # Localization parameters
    gl: Optional[str] = Field(default="au", description="Two-letter country code (e.g., 'us', 'uk', 'fr', 'au') default is 'au'")
    hl: Optional[str] = Field(default="en", description="Two-letter language code (e.g., 'en', 'es', 'fr') default is 'en'")
    currency: Optional[str] = Field(default="AUD", description="Currency code for returned prices (e.g., 'AUD', 'USD', 'EUR', 'GBP') default is 'AUD'")
    
    # Guest parameters
    adults: Optional[int] = Field(default=2, description="Number of adults")
    children: Optional[int] = Field(default=0, description="Number of children")
    children_ages: Optional[str] = Field(default=None, description="Ages of children (1-17), comma-separated (e.g., '5' or '5,8,10')")
    
    # Advanced filters
    sort_by: Optional[int] = Field(default=13, description="Sort results: 3 (lowest price), 8 (highest rating), 13 (most reviewed)")
    min_price: Optional[int] = Field(default=None, description="Lower bound of price range")
    max_price: Optional[int] = Field(default=None, description="Upper bound of price range")
    property_types: Optional[str] = Field(default=None, description="Property types to include, comma-separated (e.g., '17,12,18')")
    amenities: Optional[str] = Field(default=None, description="Amenities to include, comma-separated codes (e.g., '35,9,19'), if beachfront is included in user query, always include 11 (Beachfront)")
    rating: Optional[str] = Field(default=None, description="Rating filter: '7' (3.5+), '8' (4.0+), '9' (4.5+)")
    
    # Hotel-specific filters
    hotel_class: Optional[str] = Field(default=None, description="Hotel classes: '2' (2-star), '3' (3-star), '4' (4-star), '5' (5-star), comma-separated")
    free_cancellation: Optional[bool] = Field(default=None, description="Show results with free cancellation")
    special_offers: Optional[bool] = Field(default=None, description="Show results with special offers")
    eco_certified: Optional[bool] = Field(default=None, description="Show eco-certified results")
    
    # Vacation rental filters
    vacation_rentals: Optional[bool] = Field(default=None, description="Search for vacation rentals instead of hotels")
    bedrooms: Optional[int] = Field(default=None, description="Minimum number of bedrooms (vacation rentals only)")
    bathrooms: Optional[int] = Field(default=None, description="Minimum number of bathrooms (vacation rentals only)")
    
    # Property details
    property_token: Optional[str] = Field(default=None, description="Token for getting detailed property information")
    
    # SerpAPI parameters
    output: Optional[str] = Field(default="json", description="Output format: 'json' or 'html'")
    max_results: Optional[int] = Field(default=3, description="Maximum number of results to return")


class SerpAPIOneHotelInput(BaseModel):
    # Required parameters
    hotel_name: str = Field(description="The exact name of the hotel to search for (e.g., 'Hilton Sydney', 'Marriott Gold Coast')")
    check_in_date: str = Field(description="Check-in date in YYYY-MM-DD format (e.g., 2025-08-13)")
    check_out_date: str = Field(description="Check-out date in YYYY-MM-DD format (e.g., 2025-08-14)")
    
    # Optional search refinement
    location: Optional[str] = Field(default=None, description="City or area to narrow down the search (e.g., 'Sydney', 'New York') - helps when hotel name is common")
    
    # Localization parameters
    gl: Optional[str] = Field(default="au", description="Two-letter country code (e.g., 'us', 'uk', 'fr', 'au') default is 'au'")
    hl: Optional[str] = Field(default="en", description="Two-letter language code (e.g., 'en', 'es', 'fr') default is 'en'")
    currency: Optional[str] = Field(default="AUD", description="Currency code for returned prices (e.g., 'AUD', 'USD', 'EUR', 'GBP') default is 'AUD'")
    
    # Guest parameters
    adults: Optional[int] = Field(default=2, description="Number of adults")
    children: Optional[int] = Field(default=0, description="Number of children")
    children_ages: Optional[str] = Field(default=None, description="Ages of children (1-17), comma-separated (e.g., '5' or '5,8,10')")


class TavilyWebSearchInput(BaseModel):
    query: str = Field(description="Search query - what you want to search for on the web")
    search_depth: Optional[str] = Field(default="basic", description="Search depth: 'basic' (faster) or 'advanced' (more comprehensive)")
    topic: Optional[str] = Field(default="general", description="Search topic: 'general', 'news', or 'research'")
    max_results: Optional[int] = Field(default=5, description="Maximum number of results to return")


class PineconeRetrieveInput(BaseModel):
    query: str = Field(description="Natural language search query")
    query_vector: Optional[List[float]] = Field(default=None, description="Vector embedding for similarity search (if not provided, will be generated from query)")
    index_name: Optional[str] = Field(default="hotel-embeddings", description="Pinecone index name")
    top_k: Optional[int] = Field(default=10, description="Number of results to return")
    include_metadata: Optional[bool] = Field(default=True, description="How many hotels to return in results")


class ApifyBookingInput(BaseModel):
    # Required parameters
    check_in: str = Field(description="Check-in date in YYYY-MM-DD format (e.g., 2025-10-12)")
    check_out: str = Field(description="Check-out date in YYYY-MM-DD format (e.g., 2025-10-14)")
    location: List[str] = Field(description="List of location strings (e.g., ['gold coast', 'sydney'])")
    
    # Guest parameters
    adults: Optional[int] = Field(default=2, description="Number of adults")
    rooms: Optional[int] = Field(default=1, description="Number of rooms")
    
    # Search parameters
    currency: Optional[str] = Field(default="AUD", description="Currency code (e.g., 'AUD', 'USD', 'EUR')")
    language: Optional[str] = Field(default="en-gb", description="Language code")
    limit: Optional[int] = Field(default=5, description="Maximum number of results to return")
    sort: Optional[str] = Field(default="popular", description="Sort order: 'popular', 'price', 'rating'")
    
    # Advanced options
    entire_place: Optional[bool] = Field(default=False, description="Search for entire places only")
    flexdate: Optional[str] = Field(default="7", description="Flexible date range in days")
    health_safety: Optional[bool] = Field(default=False, description="Include health & safety info")
    sustainable: Optional[bool] = Field(default=False, description="Include sustainability info")
    
    # Include options
    includes_all: Optional[bool] = Field(default=True, description="Include all details")
    includes_description: Optional[bool] = Field(default=True, description="Include descriptions")
    includes_facilities: Optional[bool] = Field(default=True, description="Include facilities")
    includes_gallery: Optional[bool] = Field(default=True, description="Include gallery images")
    includes_policies: Optional[bool] = Field(default=True, description="Include policies")
    includes_rooms: Optional[bool] = Field(default=True, description="Include room details")
    includes_surroundings: Optional[bool] = Field(default=True, description="Include surroundings info")
    
    # Development options
    dev_dataset_clear: Optional[bool] = Field(default=False, description="Clear dataset before run")
    dev_no_strip: Optional[bool] = Field(default=False, description="Don't strip results")


# Structured Hotel Response Models
class HotelPosition(BaseModel):
    lat: float = Field(description="Latitude coordinate")
    lng: float = Field(description="Longitude coordinate")

class ExtraPrice(BaseModel):
    source: Optional[str] = Field(description="Booking source name (e.g., 'Booking.com', 'Expedia')")
    source_url: Optional[str] = Field(description="URL to the booking page")
    price: Optional[int] = Field(description="Price per night from this source")
    
class HotelResult(BaseModel):
    id: str = Field(description="Unique identifier for the hotel")
    name: str = Field(description="Hotel name")
    rating: float = Field(description="Average rating (e.g., 4.4)")
    reviews: int = Field(description="Number of reviews")
    stars: int = Field(description="Star rating (1-5)")
    address: str = Field(description="Hotel address")
    phone: str = Field(description="Contact phone number")
    features: List[str] = Field(description="List of hotel features/amenities")
    price: str = Field(description="Price per night (e.g., '$847')")
    priceLabel: str = Field(description="Price label (e.g., 'Best Price')")
    roomType: str = Field(description="Type of room")
    source: str = Field(description="Booking source (e.g., 'Booking.com')")
    sourceUrl: str = Field(description="URL to booking source")
    imageUrls: List[str] = Field(description="Hotel image URLs")
    aiNote: str = Field(description="AI-generated recommendation note")
    position: HotelPosition = Field(description="Geographic coordinates")
    extra_prices: List[ExtraPrice] = Field(description="Additional booking options with different prices and sources")


class HotelSearchResponse(BaseModel):
    resultsTitle: str = Field(description="Title describing the search criteria and results")
    results: List[HotelResult] = Field(description="List of hotel results")


class StructuredChatResponse(BaseModel):
    """Response model that can contain either a regular message or structured hotel data"""
    message: Optional[str] = Field(None, description="Regular chat message")
    hotelSearch: Optional[HotelSearchResponse] = Field(None, description="Structured hotel search results")
    session_id: str = Field(..., description="Session ID for conversation continuity")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional response metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
