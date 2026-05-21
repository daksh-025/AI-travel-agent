from typing import List, Optional
from app.models import User, UserInDB, UserProfileUpdate, UserPasswordUpdate
from app.repositories.user_repository import UserRepository
from app.core.exceptions import UserNotFoundException
from app.core.security import security_manager
from fastapi import HTTPException, status


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    async def get_user_by_id(self, user_id: str) -> User:
        """Get user by ID with business logic"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundException()
        return self.user_repository.user_in_db_to_user(user)
    
    async def get_current_user_info(self, current_user: UserInDB) -> User:
        """Get current user information"""
        return self.user_repository.user_in_db_to_user(current_user)
    
    async def get_users_paginated(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get paginated list of users"""
        users_in_db = await self.user_repository.get_users_paginated(skip, limit)
        return [self.user_repository.user_in_db_to_user(user) for user in users_in_db]
    
    async def update_user_profile(self, user_id: str, profile_update: UserProfileUpdate) -> User:
        """Update user profile information"""
        # Check if user exists
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundException()
        
        # Prepare update data
        update_data = {}
        if profile_update.username is not None:
            update_data["username"] = profile_update.username
        
        if profile_update.email is not None:
            # Check if email already exists for another user
            if await self.user_repository.check_email_exists(profile_update.email, user_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )
            update_data["email"] = profile_update.email
        
        if profile_update.language is not None:
            update_data["language"] = profile_update.language
        
        if profile_update.location is not None:
            # Convert location to dict for storage
            update_data["location"] = profile_update.location.model_dump()
        
        if profile_update.currency is not None:
            update_data["currency"] = profile_update.currency
        
        if profile_update.preferences is not None:
            # Convert preferences to dict for storage
            update_data["preferences"] = profile_update.preferences.model_dump()
        
        # Update user if there are changes
        if update_data:
            updated_user = await self.user_repository.update_user_profile(user_id, update_data)
            if not updated_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update user profile"
                )
            return self.user_repository.user_in_db_to_user(updated_user)
        
        # Return current user if no changes
        return self.user_repository.user_in_db_to_user(user)
    
    async def update_user_password(self, user_id: str, password_update: UserPasswordUpdate) -> bool:
        """Update user password with current password verification"""
        # Get current user
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundException()
        
        # Verify current password
        if not security_manager.verify_password(password_update.current_password, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Validate new password strength
        if not security_manager.validate_password_strength(password_update.new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password must be at least {security_manager.pwd_context.context.schemes[0].__dict__.get('min_length', 6)} characters long"
            )
        
        # Update password
        success = await self.user_repository.update_user_password(user_id, password_update.new_password)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )
        
        return True
