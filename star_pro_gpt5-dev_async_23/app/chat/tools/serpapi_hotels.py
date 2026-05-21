from typing import Dict, Any
from app.chat.tools.base import BaseTool
from app.chat.models import ToolResult
from app.core.config import settings
from serpapi import GoogleSearch
import requests

class SerpAPIHotelsTool(BaseTool):
    """Tool for searching hotels and getting property details using SerpAPI Google Hotels"""
    
    def __init__(self):
        super().__init__(
            name="serpapi_hotels",
            description="""Search for hotels and vacation rentals using Google Hotels API via SerpAPI.

🎯 USAGE GUIDANCE:
- Always extract dates from user queries and convert to YYYY-MM-DD format
- If user mentions specific amenities (wifi, pool, spa, etc.), include relevant amenity codes
- For beachfront requests, always include amenity code '11'
- Use hotel_class for star rating requests (e.g., "5-star" → hotel_class: "5")
- Set appropriate currency based on location (AUD for Australia, USD for US, etc.)

📝 INPUT FORMATS:
1. Structured JSON (recommended for complex queries):
{
  "query": "5-star hotel in Sydney CBD",
  "check_in_date": "2024-10-12",
  "check_out_date": "2024-10-15",
  "adults": 2,
  "children": 0,
  "hotel_class": "5",
  "amenities": "35,9,7",
  "max_price": 300,
  "currency": "AUD",
  "sort_by": 13,
  "max_results": 3
}

2. Natural language string (for simple queries):
"5-star hotel in Sydney CBD for 2 adults from Oct 12-15"

✅ REQUIRED PARAMETERS:
- query: str - Search query (anything you'd use in Google Hotels search)
- check_in_date: str - YYYY-MM-DD format (e.g., "2025-08-13")
- check_out_date: str - YYYY-MM-DD format (e.g., "2025-08-14")

⚙️ OPTIONAL PARAMETERS:
- gl: str - Country code (e.g., 'au', 'us', 'uk') - default: 'au'
- hl: str - Language code (e.g., 'en', 'es', 'fr') - default: 'en'
- currency: str - Currency for prices (e.g., 'AUD', 'USD', 'EUR') - default: 'AUD'
- adults: int - Number of adults - default: 2
- children: int - Number of children - default: 0
- children_ages: str - Ages of children, comma-separated (e.g., '5,8,10')
- sort_by: int - Sort results: 3 (lowest price), 8 (highest rating), 13 (most reviewed) - default: 13
- min_price: int - Lower bound of price range
- max_price: int - Upper bound of price range
- property_types: str - Property type codes, comma-separated (e.g., '17,12,18')
- amenities: str - Amenity codes, comma-separated (e.g., '35,9,7' for wifi, breakfast, fitness)
- rating: str - Rating filter: '7' (3.5+), '8' (4.0+), '9' (4.5+)
- hotel_class: str - Star ratings: '2', '3', '4', '5', comma-separated
- free_cancellation: bool - Show results with free cancellation
- special_offers: bool - Show results with special offers
- eco_certified: bool - Show eco-certified results
- vacation_rentals: bool - Search vacation rentals instead of hotels
- bedrooms: int - Minimum bedrooms (vacation rentals only)
- bathrooms: int - Minimum bathrooms (vacation rentals only)
- max_results: int - Maximum results to return - default: 3

🏨 AMENITY CODES (use when user mentions these features):
- 1: Free parking
- 3: Parking
- 4: Indoor pool
- 5: Outdoor pool
- 6: Pool
- 7: Fitness center/gym
- 8: Restaurant
- 9: Free breakfast
- 10: Spa
- 11: Beachfront (ALWAYS include for beach requests)
- 12: Child-friendly
- 15: Bar
- 19: Pet-friendly
- 22: Room service
- 35: Free Wi-Fi
- 40: Air-conditioned
- 52: All-inclusive available
- 53: Wheelchair accessible
- 61: EV charger

🏢 PROPERTY TYPE CODES:
- 13: Boutique hotels
- 14: Hostels
- 15: Inns
- 16: Motels
- 17: Resorts
- 18: Spa hotels
- 19: Bed and breakfasts
- 20: Other
- 21: Apartment hotels
- 22: Minshuku
- 23: Japanese-style business hotels
- 24: Ryokan

⚠️ IMPORTANT NOTES:
- Dates must be in YYYY-MM-DD format
- All numeric parameters should be integers, not strings
- Boolean parameters should be true/false, not strings
- The tool returns real-time pricing and availability data
- Results include booking links and detailed property information"""
        )
        self.api_key = settings.serpapi_api_key
        
        # Define all supported parameters and their mappings
        self.parameter_mappings = {
            # Search Query - Fix the mapping to match actual input parameter
            "q": "query",
            
            # Localization
            "gl": "gl",
            "hl": "hl", 
            "currency": "currency",
            
            # Advanced Parameters
            "check_in_date": "check_in_date",
            "check_out_date": "check_out_date",
            "adults": "adults",
            "children": "children",
            "children_ages": "children_ages",
            
            # Advanced Filters
            "sort_by": "sort_by",
            "min_price": "min_price",
            "max_price": "max_price",
            "property_types": "property_types",
            "amenities": "amenities",
            "rating": "rating",
            
            # Hotels Filters
            "brands": "brands",
            "hotel_class": "hotel_class",
            "free_cancellation": "free_cancellation",
            "special_offers": "special_offers",
            "eco_certified": "eco_certified",
            
            # Vacation Rentals Filters
            "vacation_rentals": "vacation_rentals",
            "bedrooms": "bedrooms",
            "bathrooms": "bathrooms",
            
            # Pagination
            "next_page_token": "next_page_token",
            
            # Property Details
            "property_token": "property_token",
            
            # SerpAPI Parameters
            "engine": "engine",
            "async": "async_mode",
            "zero_trace": "zero_trace",
            "output": "output",
            "max_results": "max_results"
        }
        
        # Define sort options
        self.sort_options = {
            "lowest_price": "3",
            "highest_rating": "8", 
            "most_reviewed": "13",
            "relevance": "default"
        }
        
        # Define rating options
        self.rating_options = {
            "3.5_plus": "7",
            "4.0_plus": "8",
            "4.5_plus": "9"
        }
        
        # Define hotel class options
        self.hotel_class_options = {
            "2_star": "2",
            "3_star": "3", 
            "4_star": "4",
            "5_star": "5"
        }
                
        # Define amenity mappings based on official SerpAPI amenities
        self.amenity_mappings = {
            # Official SerpAPI amenity codes
            "free_parking": "1",
            "parking": "3", 
            "indoor_pool": "4",
            "outdoor_pool": "5",
            "pool": "6",
            "fitness_center": "7",
            "fitness": "7",
            "gym": "7",
            "restaurant": "8",
            "free_breakfast": "9",
            "breakfast": "9",
            "spa": "10",
            "beach_access": "11",
            "beach": "11",
            "child_friendly": "12",
            "kid_friendly": "12",
            "children": "12",
            "bar": "15",
            "pet_friendly": "19",
            "pets": "19",
            "room_service": "22",
            "free_wifi": "35",
            "wifi": "35",
            "free_wi_fi": "35",
            "air_conditioned": "40",
            "air_conditioning": "40",
            "ac": "40",
            "all_inclusive": "52",
            "all_inclusive_available": "52",
            "wheelchair_accessible": "53",
            "wheelchair": "53",
            "accessible": "53",
            "ev_charger": "61",
            "electric_vehicle_charger": "61",
            "charging": "61"
        }
    
    async def execute(self, input_data) -> ToolResult:
        """
        Execute hotel search using Google Hotels API
        
        Args:
            input_data: Either a string (natural language query) or a dictionary containing:
                - query: Search query (required)
                - check_in_date: Check-in date YYYY-MM-DD (required)
                - check_out_date: Check-out date YYYY-MM-DD (required)
                - All other optional parameters as per SerpAPI documentation
        """
        try:
            if not self.api_key:
                return ToolResult(
                    tool_name=self.name,
                    result="SerpAPI key not configured. Please add SERPAPI_API_KEY to your environment variables.",
                    metadata={"error": "API key not configured"}
                )
            
            # Handle string input (natural language query)
            if isinstance(input_data, str):
                # For string input, we'll need to parse it and set default dates
                from datetime import datetime, timedelta
                tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                day_after = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
                
                input_data = {
                    "query": input_data,
                    "check_in_date": tomorrow,
                    "check_out_date": day_after
                }
            
            # Check for required parameters
            if not input_data.get("query"):
                return ToolResult(
                    tool_name=self.name,
                    result="Missing required parameter: 'query'",
                    metadata={"error": "Missing query parameter"}
                )
            
            if not input_data.get("check_in_date"):
                return ToolResult(
                    tool_name=self.name,
                    result="Missing required parameter: 'check_in_date'",
                    metadata={"error": "Missing check_in_date parameter"}
                )
            
            if not input_data.get("check_out_date"):
                return ToolResult(
                    tool_name=self.name,
                    result="Missing required parameter: 'check_out_date'",
                    metadata={"error": "Missing check_out_date parameter"}
                )
            
            # Apply travel crew defaults if adults/children not specified
            input_data = await self._apply_travel_crew_defaults(input_data)
            
            return await self._search_hotels(input_data)
                
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                result=f"Error processing hotel request: {str(e)}",
                metadata={"error": str(e)}
            )
    
    async def _apply_travel_crew_defaults(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply travel crew defaults for adults/children if not specified"""
        # If adults and children are already specified, don't override
        if input_data.get("adults") is not None and input_data.get("children") is not None:
            return input_data
        
        # Try to get user context from the current request context (if available)
        # This is a fallback approach since the tool doesn't have direct access to user context
        try:
            # Check if there's a way to get user preferences from context
            # For now, we'll apply reasonable defaults based on common travel crew patterns
            
            # If only adults is missing, apply travel crew default
            if input_data.get("adults") is None:
                # Default based on common travel patterns
                # This could be enhanced to read from user preferences if context is available
                input_data["adults"] = 2  # Default couple
            
            # If only children is missing, apply travel crew default
            if input_data.get("children") is None:
                input_data["children"] = 0  # Default no children
                
            # Note: The actual travel crew logic is handled in the system prompt
            # which instructs the LLM to use appropriate guest counts
            
        except Exception as e:
            # Fallback to defaults if there's any error
            if input_data.get("adults") is None:
                input_data["adults"] = 2
            if input_data.get("children") is None:
                input_data["children"] = 0
        
        return input_data
    
    async def _search_hotels(self, input_data: Dict[str, Any]) -> ToolResult:
        """Search for hotels based on structured parameters"""
        try:
            # Build API parameters directly from input_data with explicit handling
            api_params = {
                "engine": "google_hotels",
                "api_key": self.api_key,
                "q": input_data.get("query", ""),
                "check_in_date": input_data.get("check_in_date"),
                "check_out_date": input_data.get("check_out_date"),
                "adults": input_data.get("adults", 2),
                "children": input_data.get("children", 0),
                "gl": input_data.get("gl", "au"),
                "hl": input_data.get("hl", "en"),
                "currency": input_data.get("currency", "AUD"),
                "min_price": input_data.get("min_price"),
                "max_price": input_data.get("max_price"),
                "property_types": input_data.get("property_types"),
                "amenities": input_data.get("amenities"),
                "rating": input_data.get("rating"),
                "brands": input_data.get("brands"),
                "hotel_class": input_data.get("hotel_class"),
                "free_cancellation": input_data.get("free_cancellation"),
                "special_offers": input_data.get("special_offers"),
                "eco_certified": input_data.get("eco_certified"),
                "vacation_rentals": input_data.get("vacation_rentals"),
                "bedrooms": input_data.get("bedrooms"),
                "bathrooms": input_data.get("bathrooms"),
                "next_page_token": input_data.get("next_page_token"),
                "async": input_data.get("async_mode"),
                "zero_trace": input_data.get("zero_trace"),
                "output": input_data.get("output", "json")
            }
            
            # Remove None values
            api_params = {k: v for k, v in api_params.items() if v is not None}
            
            # Use SerpAPI library
            search = GoogleSearch(api_params)
            data = search.get_dict()

            limited_properties = data.get("properties", [])[:input_data.get("max_results", 3)]

            property_details_links = []
            for property in limited_properties:
                property_details_links.append(property.get('serpapi_property_details_link'))


            properties = limited_properties
            # Initialize extra_prices for all properties
            for property in properties:
                property["extra_prices"] = []

            for property_details_link in property_details_links:
                property_index = property_details_links.index(property_details_link)
                response = requests.get(property_details_link, params={"api_key": self.api_key})
                property_data = response.json()
                
                # Set basic property details
                properties[property_index]["link"] = property_data.get('link')
                properties[property_index]["address"] = property_data.get('address')
                properties[property_index]["phone"] = property_data.get('phone')
                
                prices = property_data.get('prices')
                if prices is None:
                    properties[property_index]["source"] = property_data.get('source')
                    properties[property_index]["source_url"] = property_data.get('link')
                    continue
                
                # Find the matching price and collect extra prices
                found_price = False
                extra_prices = []
                
                for price in prices:
                    price_rate = price.get('rate_per_night', {}).get('extracted_lowest')
                    property_rate = properties[property_index].get("rate_per_night", {}).get("extracted_lowest")
                    
                    if not found_price and price_rate == property_rate:
                        # This is the main price - set as source
                        properties[property_index]["source"] = price.get('source')
                        properties[property_index]["source_url"] = price.get('link')
                        found_price = True
                    elif len(extra_prices) < 3:
                        # This is an extra price - add to extra_prices list
                        extra_price = {
                            "source": price.get('source'),
                            "source_url": price.get('link'),
                            "price": price.get('rate_per_night', {}).get('extracted_lowest')
                        }
                        extra_prices.append(extra_price)
                
                
                # If no matching price found, use the first price as source
                if not found_price and prices:
                    properties[property_index]["source"] = prices[0].get('source')
                    properties[property_index]["source_url"] = prices[0].get('link')
                    properties[property_index]["price"] = prices[0].get('rate_per_night', {}).get('extracted_lowest')
                    # Remove the first price from extra_prices since it's now the main source
                    if extra_prices:
                        extra_prices.pop(0)
                
                
                # Check if current property price is higher than any in extra_prices and swap with cheapest
                if extra_prices:
                    def normalize_price(price):
                        """Normalize price to float for comparison. Handles $xxx format."""
                        if price is None:
                            return float('inf')
                        if isinstance(price, (int, float)):
                            return float(price)
                        if isinstance(price, str):
                            # Remove $ and other currency symbols, commas, spaces
                            cleaned = price.replace('$', '').replace(',', '').replace(' ', '').strip()
                            try:
                                return float(cleaned)
                            except ValueError:
                                return float('inf')
                        return float('inf')
                    
                    current_price = properties[property_index].get("rate_per_night", {}).get("extracted_lowest")
                    if current_price is not None:
                        current_price_normalized = normalize_price(current_price)
                        
                        # Find the cheapest price in extra_prices
                        cheapest_extra = min(extra_prices, key=lambda x: normalize_price(x.get("price")))
                        cheapest_price = cheapest_extra.get("price")
                        cheapest_price_normalized = normalize_price(cheapest_price)
                        
                        print(f"DEBUG: Current price: {current_price} (normalized: {current_price_normalized})")
                        print(f"DEBUG: Cheapest extra price: {cheapest_price} (normalized: {cheapest_price_normalized})")
                        print(f"DEBUG: Extra prices: {[p.get('price') for p in extra_prices]}")
                        
                        # If current property price is higher than cheapest extra price, swap them
                        if cheapest_price is not None and current_price_normalized > cheapest_price_normalized:
                            print(f"DEBUG: Swapping prices - current ({current_price}) > cheapest ({cheapest_price})")
                            
                            # Store current property's source info
                            current_source = properties[property_index].get("source")
                            current_source_url = properties[property_index].get("source_url")
                            
                            # Update property with cheapest extra price info
                            properties[property_index]["source"] = cheapest_extra.get("source")
                            properties[property_index]["source_url"] = cheapest_extra.get("source_url")
                            properties[property_index]["price"] = '$' + str(cheapest_price)
                            # Also update the rate_per_night to maintain consistency
                            if "rate_per_night" not in properties[property_index]:
                                properties[property_index]["rate_per_night"] = {}
                            properties[property_index]["rate_per_night"]["extracted_lowest"] = cheapest_price
                            
                            # Replace cheapest extra with current property info
                            cheapest_extra["source"] = current_source
                            cheapest_extra["source_url"] = current_source_url
                            cheapest_extra["price"] = current_price_normalized
                        else:
                            print(f"DEBUG: No swap needed - current ({current_price}) <= cheapest ({cheapest_price})")
                
                # Set the extra_prices for this property
                properties[property_index]["extra_prices"] = extra_prices

            # Check for API errors
            if data.get("error"):
                error_message = data["error"]
                # Handle "no results" case as empty results rather than error
                if "hasn't returned any results" in error_message or "no results" in error_message.lower():
                    result = {"properties": []}
                    import json
                    json_result = json.dumps(result, default=str)
                    return ToolResult(
                        tool_name=self.name,
                        result=json_result,
                        metadata={
                            "properties_count": 0,
                            "search_params": api_params,
                            "note": "No hotels found for the search criteria"
                        }
                    )
                else:
                    # Return actual API errors
                    return ToolResult(
                        tool_name=self.name,
                        result=f"SerpAPI error: {error_message}",
                        metadata={"error": error_message}
                    )

            result = {}
            result["properties"] = properties
            
            # Return the raw JSON data for the agent to process
            import json
            json_result = json.dumps(result, default=str)
            
            return ToolResult(
                tool_name=self.name,
                result=json_result,
                metadata={
                    "properties_count": len(properties),
                    "search_params": api_params,
                    "note": "No hotels found" if len(properties) == 0 else None
                }
            )
                    
        except Exception as e:
            print(f"Error searching hotels: {str(e)}")
            return ToolResult(
                tool_name=self.name,
                result=f"Error searching hotels: {str(e)}",
                metadata={"error": str(e)}
            )
    