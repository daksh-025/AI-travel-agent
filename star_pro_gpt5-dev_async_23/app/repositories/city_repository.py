from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.city import City


class CityRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def search_cities(self, query: str) -> List[City]:
        """
        Search cities by name (case-insensitive partial match)
        Returns all matching cities
        """
        # Create case-insensitive regex pattern for partial matching
        regex_pattern = {"$regex": query, "$options": "i"}
        
        # Search in both city and city_ascii fields
        search_filter = {
            "$or": [
                {"city": regex_pattern},
                {"city_ascii": regex_pattern}
            ]
        }
        
        # Get all matching results
        cities = []
        cursor = (
            self.db.cities
            .find(search_filter, {"_id": 0})  # Exclude _id field
            .sort("city", 1)  # Sort alphabetically by city name
        )
        
        async for city_data in cursor:
            # Handle NaN values in city_ascii field
            if city_data.get('city_ascii') is None or str(city_data.get('city_ascii')).lower() == 'nan':
                city_data['city_ascii'] = city_data.get('city', '')
            city = City(**city_data)
            cities.append(city)
        
        return cities
    
    async def bulk_insert_cities(self, cities_data: List[dict]) -> int:
        """Bulk insert cities into database"""
        if not cities_data:
            return 0
        
        result = await self.db.cities.insert_many(cities_data)
        return len(result.inserted_ids)
    
    async def get_total_cities_count(self) -> int:
        """Get total number of cities in database"""
        return await self.db.cities.count_documents({})
    
    async def clear_all_cities(self) -> int:
        """Clear all cities from database (for data refresh)"""
        result = await self.db.cities.delete_many({})
        return result.deleted_count
