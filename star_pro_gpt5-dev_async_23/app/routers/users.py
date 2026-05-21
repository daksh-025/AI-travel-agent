from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.models import User, UserProfileUpdate, UserPasswordUpdate, UserProfileUpdateResponse
from app.services.user_service import UserService
from app.dependencies import get_user_service, get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Get current user information"""
    return await user_service.get_current_user_info(current_user)


@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    user_service: UserService = Depends(get_user_service),
    current_user = Depends(get_current_user)
):
    """Get user by ID (requires authentication)"""
    return await user_service.get_user_by_id(user_id)


@router.get("/", response_model=List[User])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    user_service: UserService = Depends(get_user_service),
    current_user = Depends(get_current_user)
):
    """Get all users (paginated) - requires authentication"""
    return await user_service.get_users_paginated(skip, limit)


@router.put("/me/profile", response_model=UserProfileUpdateResponse)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Update current user's profile information
    
    - **username**: Optional new username
    - **email**: Optional new email address (must be unique)
    - **language**: Optional language preference (e.g., "au", "us", "es", "fr", etc.)
    - **location**: Optional location with city and country
    - **currency**: Optional currency preference (e.g., "aud", "usd", "eur", "gbp", etc.)
    - **preferences**: Optional travel and accommodation preferences including:
        - adults, children, childrenAgeList
        - tripType, otherTripType
        - budget, budgetType
        - minStarRating, searchPreferences
    
    At least one field must be provided for update.
    """
    try:
        updated_user = await user_service.update_user_profile(current_user.id, profile_update)
        return UserProfileUpdateResponse(
            message="Profile updated successfully",
            user=updated_user
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating profile: {str(e)}"
        )


@router.put("/me/password")
async def update_user_password(
    password_update: UserPasswordUpdate,
    current_user = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Update current user's password
    
    - **current_password**: Current password for verification
    - **new_password**: New password (minimum 6 characters)
    
    The current password must be verified before the new password is set.
    """
    try:
        success = await user_service.update_user_password(current_user.id, password_update)
        if success:
            return {"message": "Password updated successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating password: {str(e)}"
        )
