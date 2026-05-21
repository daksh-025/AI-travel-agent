from pydantic import BaseModel, Field


class City(BaseModel):
    """City model for API responses"""
    city: str = Field(..., description="City name")
    city_ascii: str = Field(..., description="ASCII version of city name")
    country: str = Field(..., description="Country name")


class CitySearchResponse(BaseModel):
    """Response model for city search"""
    cities: list[City] = Field(..., description="List of matching cities")
