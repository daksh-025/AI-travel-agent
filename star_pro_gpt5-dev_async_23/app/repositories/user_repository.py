from datetime import datetime
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.models import UserCreate, UserInDB, User
from app.core.security import security_manager


class UserRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def get_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email from database"""
        user_data = await self.db.users.find_one({"email": email})
        if user_data:
            user_data["id"] = str(user_data["_id"])
            return UserInDB(**user_data)
        return None
    
    async def get_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Get user by ID from database"""
        try:
            user_data = await self.db.users.find_one({"_id": ObjectId(user_id)})
            if user_data:
                user_data["id"] = str(user_data["_id"])
                return UserInDB(**user_data)
        except:
            pass
        return None
    
    async def create_user(self, user: UserCreate) -> UserInDB:
        """Create a new user in database"""
        hashed_password = security_manager.get_password_hash(user.password)
        now = datetime.now(datetime.timezone.utc)
        
        user_data = {
            "email": user.email,
            "username": user.username,
            "password": hashed_password,
            "is_active": True,
            "language": "English (AU)",  # Default language
            "location": None,  # Default location
            "currency": "AUD",  # Default currency
            "preferences": None,  # Default preferences
            "created_at": now,
            "updated_at": now
        }
        
        result = await self.db.users.insert_one(user_data)
        user_data["id"] = str(result.inserted_id)
        return UserInDB(**user_data)
    
    async def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        """Authenticate user with email and password"""
        user = await self.get_by_email(email)
        if not user:
            return None
        if not security_manager.verify_password(password, user.password):
            return None
        return user
    
    async def get_users_paginated(self, skip: int = 0, limit: int = 100) -> List[UserInDB]:
        """Get paginated list of users from database"""
        users = []
        cursor = self.db.users.find().skip(skip).limit(limit)
        async for user_data in cursor:
            user_data["id"] = str(user_data["_id"])
            user = UserInDB(**user_data)
            users.append(user)
        return users
    
    async def update_user_profile(self, user_id: str, update_data: dict) -> Optional[UserInDB]:
        """Update user profile information"""
        try:
            result = await self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            # Return updated user even if no fields were modified (matched_count > 0)
            if result.matched_count > 0:
                return await self.get_by_id(user_id)
        except Exception as e:
            print(f"Error updating user profile: {e}")
            import traceback
            traceback.print_exc()
        return None
    
    async def update_user_password(self, user_id: str, new_password: str) -> bool:
        """Update user password"""
        try:
            hashed_password = security_manager.get_password_hash(new_password)
            result = await self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {
                    "password": hashed_password,
                    "updated_at": datetime.now(datetime.timezone.utc)
                }}
            )
            return result.modified_count > 0
        except:
            return False

    async def create_password_reset_token(self, email: str, token: str, expires_at: datetime) -> bool:
        """Store a password reset token for a user"""
        user = await self.get_by_email(email)
        if not user:
            return False
        doc = {
            "user_id": ObjectId(user.id),
            "email": email,
            "token": token,
            "expires_at": expires_at,
            "used": False,
            "created_at": datetime.now(datetime.timezone.utc)
        }
        await self.db.password_reset_tokens.insert_one(doc)
        return True

    async def consume_password_reset_token(self, token: str) -> Optional[UserInDB]:
        """Validate and consume a reset token; returns the user if valid"""
        doc = await self.db.password_reset_tokens.find_one({"token": token, "used": False})
        if not doc:
            return None
        if doc.get("expires_at") and doc["expires_at"] < datetime.now(datetime.timezone.utc):
            return None
        # Mark as used
        await self.db.password_reset_tokens.update_one({"_id": doc["_id"]}, {"$set": {"used": True, "used_at": datetime.now(datetime.timezone.utc)}})
        user = await self.get_by_id(str(doc["user_id"]))
        return user
    
    async def check_email_exists(self, email: str, exclude_user_id: str = None) -> bool:
        """Check if email already exists (excluding current user)"""
        query = {"email": email}
        if exclude_user_id:
            query["_id"] = {"$ne": ObjectId(exclude_user_id)}
        
        user_data = await self.db.users.find_one(query)
        return user_data is not None

    def user_in_db_to_user(self, user_in_db: UserInDB) -> User:
        """Convert UserInDB to User model"""
        return User(
            id=user_in_db.id,
            email=user_in_db.email,
            username=user_in_db.username,
            is_active=user_in_db.is_active,
            language=user_in_db.language,
            location=user_in_db.location,
            currency=user_in_db.currency,
            preferences=user_in_db.preferences,
            created_at=user_in_db.created_at,
            updated_at=user_in_db.updated_at
        )
