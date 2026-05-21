from typing import Optional
from app.models.travel_preferences import (
    TravelPreferences, 
    TravelCrewType, 
    TripLength, 
    AccommodationPriority, 
    HolidayVibe, 
    PlanningStyle, 
    TravelNonNegotiable,
    TravellerType
)


class TravellerTypeService:
    """Service for determining traveller type based on travel preferences using the quiz decision map"""
    
    @staticmethod
    def determine_traveller_type(preferences: TravelPreferences) -> TravellerType:
        """
        Determine traveller type based on the quiz decision map logic.
        
        Decision Map Logic:
        1. If Q1 = Business → Business Traveller (override)
        2. If Q1 = Family (kids) → Family Holidaymaker, unless Q4 = Hiking (Adventure) or Q3 = Price (Budget-conscious family)
        3. If Q1 = Couple → Check Q4 and Q3 for Luxury Seeker, Couples on Getaways, or Budget-Conscious
        4. If Q1 = Solo → Check Q4 and Q3 for Adventure, Cultural, Budget-Conscious, or Solo Explorer
        5. If Q1 = Friends/group → Check Q4, Q6, Q2 for Event-Goer, Group Planner, or Frequent Short-Tripper
        6. Default → Frequent Short-Tripper (catch-all)
        """
        
        # Q1: Travel crew (primary filter)
        travel_crew = preferences.travel_crew
        holiday_vibe = preferences.holiday_vibe
        accommodation_priority = preferences.accommodation_priority
        trip_length = preferences.trip_length
        planning_style = preferences.planning_style
        travel_non_negotiable = preferences.travel_non_negotiable
        
        # Rule 1: Business override
        if TravelCrewType.BUSINESS in travel_crew:
            return TravellerType.BUSINESS_TRAVELLER
        
        # Rule 2: Family with kids
        if TravelCrewType.FAMILY in travel_crew:
            # Check if it's adventure-focused family (Q4 = Hiking/nature)
            if HolidayVibe.ADVENTURE_NATURE in holiday_vibe:
                return TravellerType.ADVENTURE_OUTDOOR_ENTHUSIAST
            
            # Check if it's budget-conscious family (Q3 = Price/value)
            if AccommodationPriority.PRICE_VALUE in accommodation_priority:
                return TravellerType.BUDGET_CONSCIOUS_TRAVELLER
            
            # Default family type
            return TravellerType.FAMILY_HOLIDAYMAKER
        
        # Rule 3: Couple
        if TravelCrewType.COUPLE in travel_crew:
            # Check for luxury seeker (Q4 = Spa/luxury)
            if HolidayVibe.LUXURY_SERVICE in holiday_vibe:
                return TravellerType.LUXURY_SEEKER
            
            # Check for couples getaway (Q4 = Beach/pool)
            if HolidayVibe.BEACH_RELAXATION in holiday_vibe:
                return TravellerType.COUPLES_ON_GETAWAYS
            
            # Check for budget-conscious couple (Q3 = Value)
            if AccommodationPriority.PRICE_VALUE in accommodation_priority:
                return TravellerType.BUDGET_CONSCIOUS_TRAVELLER
            
            # Default couple type (could be couples on getaways)
            return TravellerType.COUPLES_ON_GETAWAYS
        
        # Rule 4: Solo
        if TravelCrewType.SOLO in travel_crew:
            # Check for adventure enthusiast (Q4 = Hiking/nature)
            if HolidayVibe.ADVENTURE_NATURE in holiday_vibe:
                return TravellerType.ADVENTURE_OUTDOOR_ENTHUSIAST
            
            # Check for cultural traveller (Q4 = Food/culture)
            if HolidayVibe.CULTURAL_CULINARY in holiday_vibe:
                return TravellerType.CULTURAL_CULINARY_TRAVELLER
            
            # Check for budget-conscious solo (Q3 = Price/value)
            if AccommodationPriority.PRICE_VALUE in accommodation_priority:
                return TravellerType.BUDGET_CONSCIOUS_TRAVELLER
            
            # Default solo type
            return TravellerType.SOLO_EXPLORER
        
        # Rule 5: Friends/Group
        if TravelCrewType.GROUP in travel_crew:
            # Check for event-goer (Q4 = Events)
            if HolidayVibe.EVENTS_ACTIVITIES in holiday_vibe:
                return TravellerType.EVENT_GOER
            
            # Check for group trip planner (Q6 = Togetherness)
            if travel_non_negotiable == TravelNonNegotiable.TOGETHERNESS:
                return TravellerType.GROUP_TRIP_PLANNER
            
            # Check for frequent short-tripper (Q2 = Weekend)
            if TripLength.WEEKEND in trip_length:
                return TravellerType.FREQUENT_SHORT_TRIPPER
            
            # Default group type
            return TravellerType.GROUP_TRIP_PLANNER
        
        # Rule 6: Default catch-all
        return TravellerType.FREQUENT_SHORT_TRIPPER
    
    @staticmethod
    def get_traveller_type_description(traveller_type: TravellerType) -> str:
        """Get a human-readable description of the traveller type"""
        descriptions = {
            TravellerType.BUSINESS_TRAVELLER: "Business-focused traveller who prioritizes efficiency, convenience, and professional amenities",
            TravellerType.FAMILY_HOLIDAYMAKER: "Family-oriented traveller who needs kid-friendly accommodations and activities",
            TravellerType.LUXURY_SEEKER: "Premium traveller who values high-end amenities, spa services, and luxury experiences",
            TravellerType.COUPLES_ON_GETAWAYS: "Romantic traveller seeking intimate, relaxing experiences for couples",
            TravellerType.BUDGET_CONSCIOUS_TRAVELLER: "Value-focused traveller who prioritizes getting the best deal and bang for their buck",
            TravellerType.ADVENTURE_OUTDOOR_ENTHUSIAST: "Active traveller who seeks outdoor adventures, hiking, and nature-based experiences",
            TravellerType.CULTURAL_CULINARY_TRAVELLER: "Curious traveller who wants to explore local culture, cuisine, and authentic experiences",
            TravellerType.SOLO_EXPLORER: "Independent traveller who enjoys solo adventures and flexible, self-directed experiences",
            TravellerType.EVENT_GOER: "Social traveller who plans trips around festivals, concerts, and special events",
            TravellerType.GROUP_TRIP_PLANNER: "Group-focused traveller who prioritizes shared experiences and togetherness",
            TravellerType.FREQUENT_SHORT_TRIPPER: "Flexible traveller who enjoys quick getaways and spontaneous short trips"
        }
        return descriptions.get(traveller_type, "Flexible traveller with diverse interests")
    
    @staticmethod
    def get_traveller_type_recommendations(traveller_type: TravellerType) -> list[str]:
        """Get personalized recommendations based on traveller type"""
        recommendations = {
            TravellerType.BUSINESS_TRAVELLER: [
                "Prioritize properties with business centers and meeting rooms",
                "Look for locations near business districts or airports",
                "Consider properties with 24/7 room service and concierge",
                "Check for high-speed WiFi and work-friendly amenities"
            ],
            TravellerType.FAMILY_HOLIDAYMAKER: [
                "Look for properties with family-friendly amenities like pools and kids' clubs",
                "Consider accommodations with kitchenettes or family suites",
                "Check for child safety features and family activities",
                "Prioritize locations near family attractions and restaurants"
            ],
            TravellerType.LUXURY_SEEKER: [
                "Focus on 4-5 star properties with premium services",
                "Look for properties with spas, fine dining, and concierge services",
                "Consider boutique hotels and luxury resorts",
                "Check for premium amenities like butler service and exclusive experiences"
            ],
            TravellerType.COUPLES_ON_GETAWAYS: [
                "Look for romantic settings with intimate dining options",
                "Consider properties with couples' spa packages",
                "Check for adult-only areas and romantic amenities",
                "Prioritize scenic locations and romantic room types"
            ],
            TravellerType.BUDGET_CONSCIOUS_TRAVELLER: [
                "Look for package deals and off-peak rates",
                "Consider properties with free breakfast and amenities",
                "Check for last-minute deals and promotional offers",
                "Prioritize value over luxury features"
            ],
            TravellerType.ADVENTURE_OUTDOOR_ENTHUSIAST: [
                "Look for properties near hiking trails and outdoor activities",
                "Consider eco-friendly accommodations and adventure packages",
                "Check for gear storage and outdoor activity recommendations",
                "Prioritize locations with access to nature and adventure sports"
            ],
            TravellerType.CULTURAL_CULINARY_TRAVELLER: [
                "Look for properties in cultural districts and historic areas",
                "Consider accommodations with local food experiences",
                "Check for cultural tours and authentic dining recommendations",
                "Prioritize locations with museums, galleries, and local markets"
            ],
            TravellerType.SOLO_EXPLORER: [
                "Look for properties with social areas and solo-friendly activities",
                "Consider hostels or hotels with communal spaces",
                "Check for solo traveler meetups and group activities",
                "Prioritize safe, well-connected locations"
            ],
            TravellerType.EVENT_GOER: [
                "Look for properties near event venues and transportation hubs",
                "Consider accommodations with event packages and group rates",
                "Check for late-night dining and entertainment options",
                "Prioritize locations with easy access to event locations"
            ],
            TravellerType.GROUP_TRIP_PLANNER: [
                "Look for properties with group-friendly accommodations",
                "Consider hotels with meeting spaces and group activities",
                "Check for group dining options and shared amenities",
                "Prioritize locations with activities for different interests"
            ],
            TravellerType.FREQUENT_SHORT_TRIPPER: [
                "Look for properties with flexible booking policies",
                "Consider accommodations with quick check-in/out options",
                "Check for last-minute availability and short-stay packages",
                "Prioritize convenient locations and easy transportation access"
            ]
        }
        return recommendations.get(traveller_type, ["Look for properties that match your flexible travel style"])
