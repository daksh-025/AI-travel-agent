from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional
from app.database import get_database
from app.services.travel_preferences_service import TravelPreferencesService
from app.models.travel_preferences import (
    TravelPreferencesCreate,
    TravelPreferencesUpdate,
    TravelPreferencesResponse
)
from app.dependencies import get_current_user
from app.models.auth import TokenData

router = APIRouter(prefix="/travel-preferences", tags=["travel-preferences"])


@router.post("/", response_model=TravelPreferencesResponse, status_code=status.HTTP_201_CREATED)
async def create_travel_preferences(
    travel_preferences: TravelPreferencesCreate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Create new travel preferences for the authenticated user"""
    service = TravelPreferencesService(db)
    return await service.create_travel_preferences(travel_preferences, current_user.id)


@router.get("/me", response_model=TravelPreferencesResponse)
async def get_my_travel_preferences(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get travel preferences for the authenticated user"""
    service = TravelPreferencesService(db)
    preferences = await service.get_user_travel_preferences(current_user.id)
    
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No travel preferences found for this user"
        )
    
    return preferences


@router.put("/me", response_model=TravelPreferencesResponse)
async def update_my_travel_preferences(
    travel_preferences_update: TravelPreferencesUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Update travel preferences for the authenticated user"""
    service = TravelPreferencesService(db)
    preferences = await service.update_travel_preferences(current_user.id, travel_preferences_update)
    
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No travel preferences found for this user"
        )
    
    return preferences


@router.post("/me/upsert", response_model=TravelPreferencesResponse)
async def upsert_my_travel_preferences(
    travel_preferences: TravelPreferencesCreate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Create or update travel preferences for the authenticated user"""
    service = TravelPreferencesService(db)
    return await service.upsert_travel_preferences(current_user.id, travel_preferences)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_travel_preferences(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Delete travel preferences for the authenticated user"""
    service = TravelPreferencesService(db)
    success = await service.delete_travel_preferences(current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No travel preferences found for this user"
        )


@router.get("/me/analysis")
async def get_my_preferences_analysis(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get analysis and insights for the authenticated user's travel preferences"""
    service = TravelPreferencesService(db)
    return await service.analyze_user_preferences(current_user.id)


@router.get("/", response_model=List[TravelPreferencesResponse])
async def get_all_travel_preferences(
    skip: int = 0,
    limit: int = 100,
    travel_crew: Optional[str] = None,
    trip_length: Optional[str] = None,
    accommodation_priority: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get all travel preferences with optional filtering (admin only)"""
    # TODO: Add admin role check here
    service = TravelPreferencesService(db)
    
    if travel_crew:
        return await service.get_by_travel_crew(travel_crew, skip, limit)
    elif trip_length:
        return await service.get_by_trip_length(trip_length, skip, limit)
    elif accommodation_priority:
        return await service.get_by_accommodation_priority(accommodation_priority, skip, limit)
    else:
        return await service.get_all_travel_preferences(skip, limit)


@router.get("/{user_id}", response_model=TravelPreferencesResponse)
async def get_user_travel_preferences(
    user_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get travel preferences for a specific user (admin only)"""
    # TODO: Add admin role check here
    service = TravelPreferencesService(db)
    preferences = await service.get_user_travel_preferences(user_id)
    
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No travel preferences found for this user"
        )
    
    return preferences


@router.get("/{user_id}/analysis")
async def get_user_preferences_analysis(
    user_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get analysis and insights for a specific user's travel preferences (admin only)"""
    # TODO: Add admin role check here
    service = TravelPreferencesService(db)
    return await service.analyze_user_preferences(user_id)

