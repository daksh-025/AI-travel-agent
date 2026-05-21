from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.travel_preferences import TravelPreferences, TravelPreferencesCreate, TravelPreferencesUpdate
from app.database import get_database
from bson import ObjectId
from datetime import datetime


class TravelPreferencesRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.travel_preferences

    async def create(self, travel_preferences: TravelPreferencesCreate, user_id: str) -> TravelPreferences:
        """Create new travel preferences for a user"""
        travel_prefs_dict = travel_preferences.dict()
        travel_prefs_dict["user_id"] = user_id
        travel_prefs_dict["created_at"] = datetime.utcnow()
        travel_prefs_dict["updated_at"] = datetime.utcnow()
        
        result = await self.collection.insert_one(travel_prefs_dict)
        travel_prefs_dict["_id"] = result.inserted_id
        
        return TravelPreferences(**travel_prefs_dict)

    async def get_by_user_id(self, user_id: str) -> Optional[TravelPreferences]:
        """Get travel preferences by user ID"""
        doc = await self.collection.find_one({"user_id": user_id})
        if doc:
            return TravelPreferences(**doc)
        return None

    async def update(self, user_id: str, travel_preferences_update: TravelPreferencesUpdate) -> Optional[TravelPreferences]:
        """Update existing travel preferences for a user"""
        update_data = travel_preferences_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        result = await self.collection.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            return await self.get_by_user_id(user_id)
        return None

    async def upsert(self, user_id: str, travel_preferences: TravelPreferencesCreate) -> TravelPreferences:
        """Create or update travel preferences for a user"""
        existing = await self.get_by_user_id(user_id)
        if existing:
            # Convert create model to update model
            update_data = TravelPreferencesUpdate(**travel_preferences.dict())
            updated = await self.update(user_id, update_data)
            if updated:
                return updated
            # Fallback to create if update failed
            return await self.create(travel_preferences, user_id)
        else:
            return await self.create(travel_preferences, user_id)

    async def delete(self, user_id: str) -> bool:
        """Delete travel preferences for a user"""
        result = await self.collection.delete_one({"user_id": user_id})
        return result.deleted_count > 0

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[TravelPreferences]:
        """Get all travel preferences with pagination"""
        cursor = self.collection.find().skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [TravelPreferences(**doc) for doc in docs]

    async def get_by_travel_crew(self, travel_crew: str, skip: int = 0, limit: int = 100) -> List[TravelPreferences]:
        """Get travel preferences filtered by travel crew type"""
        cursor = self.collection.find({"travel_crew": travel_crew}).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [TravelPreferences(**doc) for doc in docs]

    async def get_by_trip_length(self, trip_length: str, skip: int = 0, limit: int = 100) -> List[TravelPreferences]:
        """Get travel preferences filtered by trip length"""
        cursor = self.collection.find({"trip_length": trip_length}).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [TravelPreferences(**doc) for doc in docs]

    async def get_by_accommodation_priority(self, priority: str, skip: int = 0, limit: int = 100) -> List[TravelPreferences]:
        """Get travel preferences filtered by accommodation priority"""
        cursor = self.collection.find({"accommodation_priority": priority}).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [TravelPreferences(**doc) for doc in docs]

    async def get_by_id(self, preference_id: str) -> Optional[TravelPreferences]:
        """Get travel preferences by ID"""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(preference_id)})
            if doc:
                return TravelPreferences(**doc)
        except Exception:
            pass
        return None

    async def update_by_id(self, preference_id: str, travel_preferences_update: TravelPreferencesUpdate) -> Optional[TravelPreferences]:
        """Update travel preferences by ID"""
        try:
            update_data = travel_preferences_update.dict(exclude_unset=True)
            update_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.update_one(
                {"_id": ObjectId(preference_id)},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return await self.get_by_id(preference_id)
        except Exception:
            pass
        return None

    async def delete_by_id(self, preference_id: str) -> bool:
        """Delete travel preferences by ID"""
        try:
            result = await self.collection.delete_one({"_id": ObjectId(preference_id)})
            return result.deleted_count > 0
        except Exception:
            return False
