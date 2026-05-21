import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo import ASCENDING, DESCENDING
from bson import ObjectId

from app.core.config import settings
from app.models.hotel_cache import CachedHotelData, HotelCacheQuery
from app.chat.response_models import HotelResult, HotelPosition, ExtraPrice

logger = logging.getLogger(__name__)


class HotelCacheService:
    """Service for caching hotel data in MongoDB to reduce SERP API calls"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self.collection: Optional[AsyncIOMotorCollection] = None
        self.collection_name = "hotel_cache"
        self.disabled = False  # Flag to disable cache when event loop issues occur
        
    async def initialize(self):
        """Initialize MongoDB connection and create indexes"""
        try:
            self.client = AsyncIOMotorClient(
                settings.mongodb_url,
                maxPoolSize=settings.max_pool_size,
                minPoolSize=settings.min_pool_size,
                maxIdleTimeMS=settings.max_idle_time_ms,
                waitQueueTimeoutMS=settings.wait_queue_timeout_ms,
                connectTimeoutMS=settings.connect_timeout_ms,
                serverSelectionTimeoutMS=settings.server_selection_timeout_ms,
                socketTimeoutMS=settings.socket_timeout_ms,
                heartbeatFrequencyMS=settings.heartbeat_frequency_ms,
                retryWrites=settings.retry_writes,
                retryReads=settings.retry_reads
            )
            
            self.database = self.client[settings.database_name]
            self.collection = self.database[self.collection_name]
            
            # Create indexes for efficient querying
            await self._create_indexes()
            
            logger.info("🏨 HotelCacheService initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize HotelCacheService: {e}")
            raise
    
    async def _create_indexes(self):
        """Create MongoDB indexes for efficient querying"""
        try:
            # Index on hotel_name_search for fast lookups
            await self.collection.create_index(
                [("hotel_name_search", ASCENDING)],
                name="hotel_name_search_idx"
            )
            
            # Compound index on hotel_name_search and location_search
            await self.collection.create_index(
                [("hotel_name_search", ASCENDING), ("location_search", ASCENDING)],
                name="hotel_location_compound_idx"
            )
            
            # Index on cached_at for cleanup operations
            await self.collection.create_index(
                [("cached_at", DESCENDING)],
                name="cached_at_idx"
            )
            
            # Text index for fuzzy hotel name matching
            await self.collection.create_index(
                [("hotel_name_search", "text"), ("name", "text")],
                name="hotel_name_text_idx"
            )
            
            logger.info("🏨 Hotel cache indexes created successfully")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to create some indexes: {e}")
    
    async def get_cached_hotel(self, query: HotelCacheQuery) -> Optional[CachedHotelData]:
        """
        Retrieve cached hotel data if available
        
        Args:
            query: HotelCacheQuery with search parameters
            
        Returns:
            CachedHotelData if found, None otherwise
        """
        try:
            # Check if service is disabled or not initialized
            if self.disabled or self.collection is None:
                logger.warning("⚠️ HotelCacheService disabled or not initialized, skipping cache check")
                return None
            
            logger.info(f"🔍 Checking cache for hotel: '{query.hotel_name}' in location: '{query.location}'")
            
            # Create a new MongoDB client for this operation to avoid event loop issues
            temp_client = AsyncIOMotorClient(settings.mongodb_url)
            temp_db = temp_client[settings.database_name]
            temp_collection = temp_db[self.collection_name]
            
            try:
                # Build search criteria
                search_criteria = {
                    "hotel_name_search": {"$regex": f"^{query.hotel_name}$", "$options": "i"}
                }
                
                if query.location:
                    search_criteria["location_search"] = {"$regex": f"^{query.location}$", "$options": "i"}
                
                # Find the most recent cached data
                cached_doc = await temp_collection.find_one(
                    search_criteria,
                    sort=[("cached_at", DESCENDING)]
                )
                
                if cached_doc:
                    # Convert ObjectId to string for JSON serialization
                    cached_doc["_id"] = str(cached_doc["_id"])
                    
                    cached_data = CachedHotelData(**cached_doc)
                    
                    # Verify the cached data matches our query
                    if query.matches_cached_data(cached_data):
                        logger.info(f"✅ Cache HIT for hotel: '{query.hotel_name}' - Using cached data")
                        return cached_data
                    else:
                        logger.info(f"❌ Cache MISS for hotel: '{query.hotel_name}' - Cached data doesn't match query")
                        return None
                else:
                    logger.info(f"❌ Cache MISS for hotel: '{query.hotel_name}' - No cached data found")
                    return None
                    
            finally:
                # Always close the temporary client
                temp_client.close()
                
        except Exception as e:
            error_msg = str(e)
            if "attached to a different loop" in error_msg or "different loop" in error_msg:
                logger.warning(f"⚠️ Event loop mismatch detected, disabling cache service")
                self.disabled = True
            logger.error(f"❌ Error retrieving cached hotel data: {e}")
            return None
    
    async def cache_hotel_data(self, hotel_data: HotelResult, query: HotelCacheQuery) -> bool:
        """
        Cache hotel data for future use
        
        Args:
            hotel_data: HotelResult from SERP API
            query: HotelCacheQuery with search parameters
            
        Returns:
            True if cached successfully, False otherwise
        """
        try:
            # Check if service is disabled or not initialized
            if self.disabled or self.collection is None:
                logger.warning("⚠️ HotelCacheService disabled or not initialized, skipping cache storage")
                return False
            
            logger.info(f"💾 Caching hotel data for: '{query.hotel_name}'")
            
            # Create a new MongoDB client for this operation to avoid event loop issues
            temp_client = AsyncIOMotorClient(settings.mongodb_url)
            temp_db = temp_client[settings.database_name]
            temp_collection = temp_db[self.collection_name]
            
            try:
                # Convert ExtraPrice objects to dictionaries for CachedHotelData
                extra_prices_dicts = []
                if hotel_data.extra_prices:
                    for extra_price in hotel_data.extra_prices:
                        extra_prices_dicts.append({
                            "source": extra_price.source,
                            "source_url": extra_price.source_url,
                            "price": extra_price.price
                        })
                
                # Convert HotelResult to CachedHotelData
                cached_data = CachedHotelData(
                    id=hotel_data.id,
                    name=hotel_data.name,
                    link=hotel_data.link,
                    description=hotel_data.description,
                    rating=hotel_data.rating,
                    reviews=hotel_data.reviews,
                    stars=hotel_data.stars,
                    address=hotel_data.address,
                    phone=hotel_data.phone,
                    features=hotel_data.features or [],
                    price=hotel_data.price,
                    priceLabel=hotel_data.priceLabel,
                    roomType=hotel_data.roomType,
                    source=hotel_data.source,
                    sourceUrl=hotel_data.sourceUrl,
                    imageUrls=hotel_data.imageUrls or [],
                    aiNote=hotel_data.aiNote,
                    position=hotel_data.position,
                    extra_prices=extra_prices_dicts,  # Use dictionaries instead of ExtraPrice objects
                    hotel_name_search=query.hotel_name,
                    location_search=query.location,
                    search_params={
                        "check_in_date": query.check_in_date,
                        "check_out_date": query.check_out_date,
                        "adults": query.adults,
                        "children": query.children,
                        "currency": query.currency
                    }
                )
                
                # Insert into MongoDB
                result = await temp_collection.insert_one(cached_data.dict())
                
                if result.inserted_id:
                    logger.info(f"✅ Successfully cached hotel data for: '{query.hotel_name}' (ID: {result.inserted_id})")
                    return True
                else:
                    logger.error(f"❌ Failed to cache hotel data for: '{query.hotel_name}'")
                    return False
                    
            finally:
                # Always close the temporary client
                temp_client.close()
                
        except Exception as e:
            error_msg = str(e)
            if "attached to a different loop" in error_msg or "different loop" in error_msg:
                logger.warning(f"⚠️ Event loop mismatch detected, disabling cache service")
                self.disabled = True
            logger.error(f"❌ Error caching hotel data: {e}")
            return False
    
    async def convert_cached_to_hotel_result(self, cached_data: CachedHotelData) -> HotelResult:
        """
        Convert CachedHotelData back to HotelResult format
        
        Args:
            cached_data: CachedHotelData from MongoDB
            
        Returns:
            HotelResult compatible with existing code
        """
        try:
            # Convert extra_prices from dictionaries to ExtraPrice objects
            extra_prices = []
            if cached_data.extra_prices:
                for extra_price_dict in cached_data.extra_prices:
                    # Handle both dict and ExtraPrice object formats
                    if isinstance(extra_price_dict, dict):
                        extra_prices.append(ExtraPrice(
                            source=extra_price_dict.get("source"),
                            source_url=extra_price_dict.get("source_url"),
                            price=extra_price_dict.get("price")
                        ))
                    else:
                        # Already an ExtraPrice object - convert to dict first, then to ExtraPrice
                        extra_prices.append(ExtraPrice(
                            source=getattr(extra_price_dict, 'source', None),
                            source_url=getattr(extra_price_dict, 'source_url', None),
                            price=getattr(extra_price_dict, 'price', None)
                        ))
            
            # Convert position
            position = None
            if cached_data.position:
                position = HotelPosition(
                    lat=cached_data.position.lat,
                    lng=cached_data.position.lng
                )
            
            return HotelResult(
                id=cached_data.id,
                name=cached_data.name,
                link=cached_data.link,
                description=cached_data.description,
                rating=float(cached_data.rating) if cached_data.rating is not None else 4.2,  # Default to reasonable rating
                reviews=int(cached_data.reviews) if cached_data.reviews is not None else 150,  # Default to reasonable review count
                stars=int(cached_data.stars) if cached_data.stars is not None else 4,  # Default to 4 stars
                address=cached_data.address or "",
                phone=cached_data.phone or "",
                features=cached_data.features or [],
                price=cached_data.price or None,  # Use actual cached price
                priceLabel=cached_data.priceLabel or "Best Price",  # Default to "Best Price" for green color
                roomType=cached_data.roomType or "Standard Room",
                source=cached_data.source or "Direct",
                sourceUrl=cached_data.sourceUrl or cached_data.link or "",  # Fallback to link if sourceUrl missing
                imageUrls=cached_data.imageUrls or [],
                aiNote=cached_data.aiNote or "",
                position=position,
                extra_prices=extra_prices
            )
            
        except Exception as e:
            logger.error(f"❌ Error converting cached data to HotelResult: {e}")
            raise
    
    async def cleanup_old_cache(self, days_old: int = 30) -> int:
        """
        Remove cached hotel data older than specified days
        
        Args:
            days_old: Number of days after which to remove cached data
            
        Returns:
            Number of documents removed
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            result = await self.collection.delete_many({
                "cached_at": {"$lt": cutoff_date}
            })
            
            logger.info(f"🧹 Cleaned up {result.deleted_count} old cached hotel records")
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up old cache: {e}")
            return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            total_count = await self.collection.count_documents({})
            
            # Count by date ranges
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)
            
            recent_count = await self.collection.count_documents({
                "cached_at": {"$gte": week_ago}
            })
            
            monthly_count = await self.collection.count_documents({
                "cached_at": {"$gte": month_ago}
            })
            
            return {
                "total_cached_hotels": total_count,
                "recent_cached_hotels": recent_count,
                "monthly_cached_hotels": monthly_count,
                "collection_name": self.collection_name
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting cache stats: {e}")
            return {"error": str(e)}
    
    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("🏨 HotelCacheService connection closed")


# Global instance
hotel_cache_service = HotelCacheService()

# Add a safety wrapper to ensure service is initialized
async def safe_hotel_cache_operation(operation_name: str, operation_func, *args, **kwargs):
    """
    Safely execute hotel cache operations with initialization check
    """
    try:
        if hotel_cache_service.disabled:
            logger.warning(f"⚠️ HotelCacheService disabled due to event loop issues, skipping {operation_name}")
            return None
        
        if hotel_cache_service.collection is None:
            logger.warning(f"⚠️ HotelCacheService not initialized, skipping {operation_name}")
            return None
        
        # Execute the operation directly since we're using fresh MongoDB clients
        return await operation_func(*args, **kwargs)
        
    except Exception as e:
        error_msg = str(e)
        if "attached to a different loop" in error_msg or "different loop" in error_msg:
            logger.warning(f"⚠️ Event loop mismatch detected, disabling cache service")
            hotel_cache_service.disabled = True
            return None
        else:
            logger.error(f"❌ Error in {operation_name}: {e}")
            return None
