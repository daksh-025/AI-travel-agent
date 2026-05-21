from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.travel_preferences_repository import TravelPreferencesRepository
from app.models.travel_preferences import TravelPreferences, TravelPreferencesCreate, TravelPreferencesUpdate, TravelPreferencesResponse
from app.services.traveller_type_service import TravellerTypeService
from app.database import get_database


class TravelPreferencesService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.repository = TravelPreferencesRepository(db)

    async def create_travel_preferences(self, travel_preferences: TravelPreferencesCreate, user_id: str) -> TravelPreferencesResponse:
        """Create new travel preferences for a user and determine traveller type"""
        # Create the travel preferences first
        db_travel_preferences = await self.repository.create(travel_preferences, user_id)
        
        # Determine traveller type based on preferences
        traveller_type = TravellerTypeService.determine_traveller_type(db_travel_preferences)
        
        # Update the preferences with the determined traveller type
        from app.models.travel_preferences import TravelPreferencesUpdate
        update_data = TravelPreferencesUpdate(traveller_type=traveller_type)
        updated_preferences = await self.repository.update(user_id, update_data)
        
        return TravelPreferencesResponse(
            id=str(updated_preferences.id),
            user_id=updated_preferences.user_id,
            travel_crew=updated_preferences.travel_crew,
            family_details=updated_preferences.family_details,
            trip_length=updated_preferences.trip_length,
            accommodation_priority=updated_preferences.accommodation_priority,
            holiday_vibe=updated_preferences.holiday_vibe,
            planning_style=updated_preferences.planning_style,
            travel_non_negotiable=updated_preferences.travel_non_negotiable,
            accommodation_preferences=updated_preferences.accommodation_preferences,
            traveller_type=updated_preferences.traveller_type,
            created_at=updated_preferences.created_at,
            updated_at=updated_preferences.updated_at
        )

    async def get_user_travel_preferences(self, user_id: str) -> Optional[TravelPreferencesResponse]:
        """Get travel preferences for a specific user"""
        db_travel_preferences = await self.repository.get_by_user_id(user_id)
        if not db_travel_preferences:
            return None
        
        return TravelPreferencesResponse(
            id=str(db_travel_preferences.id),
            user_id=db_travel_preferences.user_id,
            travel_crew=db_travel_preferences.travel_crew,
            family_details=db_travel_preferences.family_details,
            trip_length=db_travel_preferences.trip_length,
            accommodation_priority=db_travel_preferences.accommodation_priority,
            holiday_vibe=db_travel_preferences.holiday_vibe,
            planning_style=db_travel_preferences.planning_style,
            travel_non_negotiable=db_travel_preferences.travel_non_negotiable,
            accommodation_preferences=db_travel_preferences.accommodation_preferences,
            traveller_type=db_travel_preferences.traveller_type,
            created_at=db_travel_preferences.created_at,
            updated_at=db_travel_preferences.updated_at
        )

    async def update_travel_preferences(self, user_id: str, travel_preferences_update: TravelPreferencesUpdate) -> Optional[TravelPreferencesResponse]:
        """Update existing travel preferences for a user and recalculate traveller type"""
        # Update the preferences first
        db_travel_preferences = await self.repository.update(user_id, travel_preferences_update)
        if not db_travel_preferences:
            return None
        
        # Recalculate traveller type based on updated preferences
        traveller_type = TravellerTypeService.determine_traveller_type(db_travel_preferences)
        
        # Update the traveller type if it has changed
        if db_travel_preferences.traveller_type != traveller_type:
            from app.models.travel_preferences import TravelPreferencesUpdate
            traveller_type_update = TravelPreferencesUpdate(traveller_type=traveller_type)
            db_travel_preferences = await self.repository.update(user_id, traveller_type_update)
        
        return TravelPreferencesResponse(
            id=str(db_travel_preferences.id),
            user_id=db_travel_preferences.user_id,
            travel_crew=db_travel_preferences.travel_crew,
            family_details=db_travel_preferences.family_details,
            trip_length=db_travel_preferences.trip_length,
            accommodation_priority=db_travel_preferences.accommodation_priority,
            holiday_vibe=db_travel_preferences.holiday_vibe,
            planning_style=db_travel_preferences.planning_style,
            travel_non_negotiable=db_travel_preferences.travel_non_negotiable,
            accommodation_preferences=db_travel_preferences.accommodation_preferences,
            traveller_type=db_travel_preferences.traveller_type,
            created_at=db_travel_preferences.created_at,
            updated_at=db_travel_preferences.updated_at
        )

    async def upsert_travel_preferences(self, user_id: str, travel_preferences: TravelPreferencesCreate) -> TravelPreferencesResponse:
        """Create or update travel preferences for a user and determine traveller type"""
        # Upsert the preferences first
        db_travel_preferences = await self.repository.upsert(user_id, travel_preferences)
        
        # Determine traveller type based on preferences
        traveller_type = TravellerTypeService.determine_traveller_type(db_travel_preferences)
        
        # Update the preferences with the determined traveller type
        from app.models.travel_preferences import TravelPreferencesUpdate
        update_data = TravelPreferencesUpdate(traveller_type=traveller_type)
        updated_preferences = await self.repository.update(user_id, update_data)
        
        return TravelPreferencesResponse(
            id=str(updated_preferences.id),
            user_id=updated_preferences.user_id,
            travel_crew=updated_preferences.travel_crew,
            family_details=updated_preferences.family_details,
            trip_length=updated_preferences.trip_length,
            accommodation_priority=updated_preferences.accommodation_priority,
            holiday_vibe=updated_preferences.holiday_vibe,
            planning_style=updated_preferences.planning_style,
            travel_non_negotiable=updated_preferences.travel_non_negotiable,
            accommodation_preferences=updated_preferences.accommodation_preferences,
            traveller_type=updated_preferences.traveller_type,
            created_at=updated_preferences.created_at,
            updated_at=updated_preferences.updated_at
        )

    async def delete_travel_preferences(self, user_id: str) -> bool:
        """Delete travel preferences for a user"""
        return await self.repository.delete(user_id)

    async def get_all_travel_preferences(self, skip: int = 0, limit: int = 100) -> List[TravelPreferencesResponse]:
        """Get all travel preferences with pagination"""
        db_travel_preferences = await self.repository.get_all(skip, limit)
        return [
            TravelPreferencesResponse(
                id=str(tp.id),
                user_id=tp.user_id,
                travel_crew=tp.travel_crew,
                family_details=tp.family_details,
                trip_length=tp.trip_length,
                accommodation_priority=tp.accommodation_priority,
                holiday_vibe=tp.holiday_vibe,
                planning_style=tp.planning_style,
                travel_non_negotiable=tp.travel_non_negotiable,
                accommodation_preferences=tp.accommodation_preferences,
                traveller_type=tp.traveller_type,
                created_at=tp.created_at,
                updated_at=tp.updated_at
            ) for tp in db_travel_preferences
        ]

    async def get_by_travel_crew(self, travel_crew: str, skip: int = 0, limit: int = 100) -> List[TravelPreferencesResponse]:
        """Get travel preferences filtered by travel crew type"""
        db_travel_preferences = await self.repository.get_by_travel_crew(travel_crew, skip, limit)
        return [
            TravelPreferencesResponse(
                id=str(tp.id),
                user_id=tp.user_id,
                travel_crew=tp.travel_crew,
                family_details=tp.family_details,
                trip_length=tp.trip_length,
                accommodation_priority=tp.accommodation_priority,
                holiday_vibe=tp.holiday_vibe,
                planning_style=tp.planning_style,
                travel_non_negotiable=tp.travel_non_negotiable,
                accommodation_preferences=tp.accommodation_preferences,
                traveller_type=tp.traveller_type,
                created_at=tp.created_at,
                updated_at=tp.updated_at
            ) for tp in db_travel_preferences
        ]

    async def get_by_trip_length(self, trip_length: str, skip: int = 0, limit: int = 100) -> List[TravelPreferencesResponse]:
        """Get travel preferences filtered by trip length"""
        db_travel_preferences = await self.repository.get_by_trip_length(trip_length, skip, limit)
        return [
            TravelPreferencesResponse(
                id=str(tp.id),
                user_id=tp.user_id,
                travel_crew=tp.travel_crew,
                family_details=tp.family_details,
                trip_length=tp.trip_length,
                accommodation_priority=tp.accommodation_priority,
                holiday_vibe=tp.holiday_vibe,
                planning_style=tp.planning_style,
                travel_non_negotiable=tp.travel_non_negotiable,
                accommodation_preferences=tp.accommodation_preferences,
                traveller_type=tp.traveller_type,
                created_at=tp.created_at,
                updated_at=tp.updated_at
            ) for tp in db_travel_preferences
        ]

    async def get_by_accommodation_priority(self, priority: str, skip: int = 0, limit: int = 100) -> List[TravelPreferencesResponse]:
        """Get travel preferences filtered by accommodation priority"""
        db_travel_preferences = await self.repository.get_by_accommodation_priority(priority, skip, limit)
        return [
            TravelPreferencesResponse(
                id=str(tp.id),
                user_id=tp.user_id,
                travel_crew=tp.travel_crew,
                family_details=tp.family_details,
                trip_length=tp.trip_length,
                accommodation_priority=tp.accommodation_priority,
                holiday_vibe=tp.holiday_vibe,
                planning_style=tp.planning_style,
                travel_non_negotiable=tp.travel_non_negotiable,
                accommodation_preferences=tp.accommodation_preferences,
                traveller_type=tp.traveller_type,
                created_at=tp.created_at,
                updated_at=tp.updated_at
            ) for tp in db_travel_preferences
        ]

    async def analyze_user_preferences(self, user_id: str) -> dict:
        """Analyze user travel preferences and return insights"""
        preferences = await self.get_user_travel_preferences(user_id)
        if not preferences:
            return {"error": "No preferences found for user"}
        
        analysis = {
            "travel_style": self._analyze_travel_style(preferences),
            "accommodation_needs": self._analyze_accommodation_needs(preferences),
            "planning_characteristics": self._analyze_planning_characteristics(preferences),
            "recommendations": self._generate_recommendations(preferences)
        }
        
        return analysis

    def _analyze_travel_style(self, preferences: TravelPreferencesResponse) -> dict:
        """Analyze the user's travel style based on their preferences"""
        style_mapping = {
            "solo": "Independent traveler who enjoys solo adventures",
            "couple": "Romantic getaway seeker who values togetherness",
            "family": "Family-oriented traveler who needs kid-friendly options",
            "group": "Social traveler who enjoys group experiences",
            "business": "Efficiency-focused business traveler"
        }
        
        # Handle multiple travel crew types
        crew_descriptions = []
        for crew_type in preferences.travel_crew:
            crew_descriptions.append(style_mapping.get(crew_type, "Flexible traveler"))
        
        return {
            "crew_types": preferences.travel_crew,
            "descriptions": crew_descriptions,
            "trip_length_preferences": preferences.trip_length,
            "holiday_vibes": preferences.holiday_vibe
        }

    def _analyze_accommodation_needs(self, preferences: TravelPreferencesResponse) -> dict:
        """Analyze the user's accommodation needs"""
        priority_mapping = {
            "price_value": "Budget-conscious traveler",
            "location": "Location-focused traveler",
            "style_atmosphere": "Aesthetic and experience seeker",
            "facilities_activities": "Activity-oriented traveler",
            "convenience_efficiency": "Practical and efficient traveler"
        }
        
        # Handle multiple accommodation priorities
        priority_descriptions = []
        for priority in preferences.accommodation_priority:
            priority_descriptions.append(priority_mapping.get(priority, "Balanced traveler"))
        
        return {
            "priorities": preferences.accommodation_priority,
            "descriptions": priority_descriptions,
            "must_have_features": preferences.accommodation_preferences.must_have,
            "nice_to_have_features": preferences.accommodation_preferences.nice_to_have,
            "not_important_features": preferences.accommodation_preferences.not_important,
            "custom_preferences": preferences.accommodation_preferences.custom_preferences or []
        }

    def _analyze_planning_characteristics(self, preferences: TravelPreferencesResponse) -> dict:
        """Analyze the user's planning characteristics"""
        planning_mapping = {
            "spontaneous": "Last-minute decision maker",
            "researched": "Thorough planner",
            "family_schedule": "Family schedule coordinator",
            "work_schedule": "Work schedule dependent",
            "deal_driven": "Deal hunter"
        }
        
        # Handle multiple planning styles
        planning_descriptions = []
        for planning_style in preferences.planning_style:
            planning_descriptions.append(planning_mapping.get(planning_style, "Flexible planner"))
        
        return {
            "planning_styles": preferences.planning_style,
            "descriptions": planning_descriptions,
            "non_negotiable": preferences.travel_non_negotiable
        }

    def _generate_recommendations(self, preferences: TravelPreferencesResponse) -> List[str]:
        """Generate personalized recommendations based on preferences"""
        recommendations = []
        
        # Crew-based recommendations
        if "family" in preferences.travel_crew:
            recommendations.append("Look for properties with family-friendly amenities and activities")
            if preferences.family_details and preferences.family_details.children > 0:
                recommendations.append(f"Consider properties with kid's clubs for {preferences.family_details.children} children")
        
        if "business" in preferences.travel_crew:
            recommendations.append("Prioritize properties with business facilities and convenient locations")
        
        if "solo" in preferences.travel_crew:
            recommendations.append("Consider properties that offer social opportunities and solo-friendly activities")
        
        # Trip length recommendations
        if "weekend" in preferences.trip_length:
            recommendations.append("Focus on properties within 2-3 hours travel time")
        if "long_holiday" in preferences.trip_length:
            recommendations.append("Consider properties with extensive facilities for longer stays")
        
        # Priority-based recommendations
        if "price_value" in preferences.accommodation_priority:
            recommendations.append("Look for package deals and off-peak rates")
        if "location" in preferences.accommodation_priority:
            recommendations.append("Prioritize central locations over luxury amenities")
        
        # Vibe-based recommendations
        if "adventure_nature" in preferences.holiday_vibe:
            recommendations.append("Consider properties near hiking trails and outdoor activities")
        if "luxury_service" in preferences.holiday_vibe:
            recommendations.append("Look for 4-5 star properties with premium services")
        
        # Accommodation preferences recommendations
        if preferences.accommodation_preferences.must_have:
            recommendations.append(f"Prioritize properties with these must-have features: {', '.join(preferences.accommodation_preferences.must_have)}")
        
        return recommendations
