from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from bson import ObjectId
from pydantic_core import core_schema


class PyObjectId(str):
    """Custom ObjectId for Pydantic models that serializes as string"""
    
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        return core_schema.with_info_after_validator_function(
            lambda v, info: str(v) if v else None,
            core_schema.any_schema(),
            serialization=core_schema.str_schema(),
        )
    
    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        return {"type": "string", "format": "objectid"}


class TravelCrewType(str, Enum):
    SOLO = "solo"
    COUPLE = "couple"
    FAMILY = "family"
    GROUP = "group"
    BUSINESS = "business"


class TripLength(str, Enum):
    WEEKEND = "weekend"
    WEEK = "week"
    LONG_HOLIDAY = "long_holiday"
    FLEXIBLE = "flexible"


class AccommodationPriority(str, Enum):
    PRICE_VALUE = "price_value"
    LOCATION = "location"
    STYLE_ATMOSPHERE = "style_atmosphere"
    FACILITIES_ACTIVITIES = "facilities_activities"
    CONVENIENCE_EFFICIENCY = "convenience_efficiency"


class HolidayVibe(str, Enum):
    BEACH_RELAXATION = "beach_relaxation"
    ADVENTURE_NATURE = "adventure_nature"
    CULTURAL_CULINARY = "cultural_culinary"
    LUXURY_SERVICE = "luxury_service"
    EVENTS_ACTIVITIES = "events_activities"


class PlanningStyle(str, Enum):
    SPONTANEOUS = "spontaneous"
    RESEARCHED = "researched"
    FAMILY_SCHEDULE = "family_schedule"
    WORK_SCHEDULE = "work_schedule"
    DEAL_DRIVEN = "deal_driven"


class TravelNonNegotiable(str, Enum):
    COMFORT = "comfort"
    ADVENTURE = "adventure"
    VALUE = "value"
    EFFICIENCY = "efficiency"
    TOGETHERNESS = "togetherness"


class TravellerType(str, Enum):
    """Traveller types determined by the quiz decision map"""
    BUSINESS_TRAVELLER = "business_traveller"
    FAMILY_HOLIDAYMAKER = "family_holidaymaker"
    LUXURY_SEEKER = "luxury_seeker"
    COUPLES_ON_GETAWAYS = "couples_on_getaways"
    BUDGET_CONSCIOUS_TRAVELLER = "budget_conscious_traveller"
    ADVENTURE_OUTDOOR_ENTHUSIAST = "adventure_outdoor_enthusiast"
    CULTURAL_CULINARY_TRAVELLER = "cultural_culinary_traveller"
    SOLO_EXPLORER = "solo_explorer"
    EVENT_GOER = "event_goer"
    GROUP_TRIP_PLANNER = "group_trip_planner"
    FREQUENT_SHORT_TRIPPER = "frequent_short_tripper"


class FamilyDetails(BaseModel):
    adults: int = Field(default=0, ge=0)
    children: int = Field(default=0, ge=0)
    infants: int = Field(default=0, ge=0)
    children_ages: Optional[List[int]] = Field(default=None, description="Ages of children")


class AccommodationPreferences(BaseModel):
    must_have: List[str] = Field(
        default_factory=list,
        description="Features that are absolutely required"
    )
    nice_to_have: List[str] = Field(
        default_factory=list,
        description="Features that would be great to have but not essential"
    )
    not_important: List[str] = Field(
        default_factory=list,
        description="Features that are not important to the user"
    )
    custom_preferences: Optional[List[str]] = Field(
        default=None, 
        description="User-defined preferences not in the standard list"
    )


class TravelPreferences(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=lambda: PyObjectId(str(ObjectId())), alias="_id")
    user_id: str = Field(..., description="User ID who owns these preferences")
    travel_crew: List[TravelCrewType] = Field(..., description="Types of travel crew (multiple choice)")
    family_details: Optional[FamilyDetails] = Field(default=None, description="Family composition details")
    trip_length: List[TripLength] = Field(..., description="Preferred trip lengths (multiple choice)")
    accommodation_priority: List[AccommodationPriority] = Field(..., description="Priorities for accommodation selection (multiple choice)")
    holiday_vibe: List[HolidayVibe] = Field(..., description="Preferred holiday atmospheres (multiple choice)")
    planning_style: List[PlanningStyle] = Field(..., description="How user plans trips (multiple choice)")
    travel_non_negotiable: TravelNonNegotiable = Field(..., description="Most important travel factor (single choice)")
    accommodation_preferences: AccommodationPreferences = Field(..., description="Specific accommodation requirements")
    traveller_type: Optional[TravellerType] = Field(default=None, description="Determined traveller type based on preferences")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "validate_assignment": True
    }
    
    @field_validator('id', mode='before')
    @classmethod
    def validate_object_id(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            return PyObjectId(v)
        if isinstance(v, ObjectId):
            return PyObjectId(str(v))
        return v


class TravelPreferencesCreate(BaseModel):
    travel_crew: List[TravelCrewType]
    family_details: Optional[FamilyDetails] = None
    trip_length: List[TripLength]
    accommodation_priority: List[AccommodationPriority]
    holiday_vibe: List[HolidayVibe]
    planning_style: List[PlanningStyle]
    travel_non_negotiable: TravelNonNegotiable
    accommodation_preferences: AccommodationPreferences


class TravelPreferencesUpdate(BaseModel):
    travel_crew: Optional[List[TravelCrewType]] = None
    family_details: Optional[FamilyDetails] = None
    trip_length: Optional[List[TripLength]] = None
    accommodation_priority: Optional[List[AccommodationPriority]] = None
    holiday_vibe: Optional[List[HolidayVibe]] = None
    planning_style: Optional[List[PlanningStyle]] = None
    travel_non_negotiable: Optional[TravelNonNegotiable] = None
    accommodation_preferences: Optional[AccommodationPreferences] = None
    traveller_type: Optional[TravellerType] = None


class TravelPreferencesResponse(BaseModel):
    id: str
    user_id: str
    travel_crew: List[TravelCrewType]
    family_details: Optional[FamilyDetails] = None
    trip_length: List[TripLength]
    accommodation_priority: List[AccommodationPriority]
    holiday_vibe: List[HolidayVibe]
    planning_style: List[PlanningStyle]
    travel_non_negotiable: TravelNonNegotiable
    accommodation_preferences: AccommodationPreferences
    traveller_type: Optional[TravellerType] = None
    created_at: datetime
    updated_at: datetime

