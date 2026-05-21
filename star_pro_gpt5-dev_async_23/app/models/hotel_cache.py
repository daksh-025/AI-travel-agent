from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId


class HotelPosition(BaseModel):
    """Geographic coordinates for hotel"""
    lat: float
    lng: float


class ExtraPrice(BaseModel):
    """Additional booking options with different prices and sources"""
    source: str
    source_url: str
    price: Optional[int] = Field(description="Price per night from this source")


class CachedHotelData(BaseModel):
    """Cached hotel data structure matching the hotel card requirements"""
    # Basic hotel information
    id: str = Field(description="Unique identifier for the hotel")
    name: str = Field(description="Hotel name")
    link: Optional[str] = Field(description="Hotel link")
    description: Optional[str] = Field(description="Hotel description")
    
    # Ratings and reviews
    rating: Optional[float] = Field(description="Average rating (e.g., 4.4)")
    reviews: Optional[int] = Field(description="Number of reviews")
    stars: Optional[int] = Field(description="Star rating (1-5)")
    
    # Contact information
    address: Optional[str] = Field(description="Hotel address")
    phone: Optional[str] = Field(description="Contact phone number")
    
    # Features and amenities
    features: List[str] = Field(default_factory=list, description="List of hotel features/amenities")
    
    # Pricing information
    price: Optional[str] = Field(description="Price per night (e.g., '$847')")
    priceLabel: Optional[str] = Field(description="Price label (e.g., 'Best Price')")
    roomType: Optional[str] = Field(description="Type of room")
    
    # Booking information
    source: Optional[str] = Field(description="Booking source (e.g., 'Booking.com')")
    sourceUrl: Optional[str] = Field(description="URL to booking source")
    
    # Media
    imageUrls: List[str] = Field(default_factory=list, description="Hotel image URLs")
    
    # AI generated content
    aiNote: Optional[str] = Field(description="AI-generated recommendation note")
    
    # Location
    position: Optional[HotelPosition] = Field(description="Geographic coordinates")
    
    # Additional pricing options
    extra_prices: List[ExtraPrice] = Field(default_factory=list, description="Additional booking options with different prices and sources")
    
    # Cache metadata
    cached_at: datetime = Field(default_factory=datetime.utcnow, description="When this data was cached")
    search_params: Dict[str, Any] = Field(description="Original search parameters used to find this hotel")
    hotel_name_search: str = Field(description="Hotel name used in the search")
    location_search: Optional[str] = Field(description="Location used in the search")
    
    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class HotelCacheQuery(BaseModel):
    """Query parameters for hotel cache lookup"""
    hotel_name: str
    location: Optional[str] = None
    check_in_date: Optional[str] = None
    check_out_date: Optional[str] = None
    adults: Optional[int] = None
    children: Optional[int] = None
    currency: Optional[str] = None
    
    def generate_cache_key(self) -> str:
        """Generate a unique cache key for this query"""
        # Create a normalized key based on hotel name and location
        hotel_key = self.hotel_name.lower().strip()
        location_key = self.location.lower().strip() if self.location else ""
        
        # Combine hotel name and location for uniqueness
        if location_key:
            return f"{hotel_key}|{location_key}"
        return hotel_key
    
    def matches_cached_data(self, cached_data: CachedHotelData) -> bool:
        """Check if this query matches the cached data"""
        # Check if hotel name matches (case insensitive)
        if cached_data.hotel_name_search.lower().strip() != self.hotel_name.lower().strip():
            return False
        
        # Check if location matches (if specified)
        if self.location and cached_data.location_search:
            if cached_data.location_search.lower().strip() != self.location.lower().strip():
                return False
        
        return True
