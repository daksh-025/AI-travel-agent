from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.city_repository import CityRepository
from app.models.city import City, CitySearchResponse


class CityService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.city_repository = CityRepository(db)
    
    async def search_cities(self, query: str) -> CitySearchResponse:
        """
        Search cities by name
        
        Args:
            query: Search query for city name
            
        Returns:
            CitySearchResponse with all matching cities
        """
        if not query or not query.strip():
            return CitySearchResponse(cities=[])
        
        cities = await self.city_repository.search_cities(query.strip())
        
        return CitySearchResponse(cities=cities)
    
    async def get_total_cities_count(self) -> int:
        """Get total number of cities in database"""
        return await self.city_repository.get_total_cities_count()
    
    async def import_cities_from_data(self, cities_data: List[dict]) -> int:
        """
        Import cities data into database
        
        Args:
            cities_data: List of city dictionaries with city, city_ascii, country fields
            
        Returns:
            Number of cities imported
        """
        return await self.city_repository.bulk_insert_cities(cities_data)
    
    async def refresh_cities_data(self, cities_data: List[dict]) -> int:
        """
        Refresh cities data by clearing existing data and importing new data
        
        Args:
            cities_data: List of city dictionaries with city, city_ascii, country fields
            
        Returns:
            Number of cities imported
        """
        # Clear existing data
        await self.city_repository.clear_all_cities()
        
        # Import new data
        return await self.city_repository.bulk_insert_cities(cities_data)
