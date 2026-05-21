from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models.city import CitySearchResponse
from app.services.city_service import CityService
from app.dependencies import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter(prefix="/cities", tags=["cities"])


async def get_city_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> CityService:
    """Dependency to get city service"""
    return CityService(db)


@router.get("/search", response_model=CitySearchResponse)
async def search_cities(
    q: str = Query(..., description="Search query for city name", min_length=1),
    city_service: CityService = Depends(get_city_service)
):
    """
    Search cities by name
    
    - **q**: Search query for city name (minimum 1 character)
    
    Returns all cities matching the search query.
    The search is case-insensitive and matches partial city names.
    """
    try:
        return await city_service.search_cities(q)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching cities: {str(e)}"
        )
