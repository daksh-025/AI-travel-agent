from typing import Dict, Any
from app.chat.tools.base import BaseTool
from app.chat.models import ToolResult
from app.core.config import settings
from serpapi import GoogleSearch
import requests
import logging
import json

from app.services.hotel_cache_service import hotel_cache_service, safe_hotel_cache_operation
from app.models.hotel_cache import HotelCacheQuery

logger = logging.getLogger(__name__)

class SerpAPIOneHotelTool(BaseTool):
    """Tool for getting detailed information about a specific hotel by name using SerpAPI Google Hotels"""
    
    def __init__(self):
        super().__init__(
            name="serpapi_one_hotel",
            description="""Get detailed information about a specific hotel by its name using Google Hotels API via SerpAPI.

🎯 USAGE GUIDANCE:
- This tool searches for ONE specific hotel by name and returns its detailed information
- Always extract dates from user queries and convert to YYYY-MM-DD format
- Provide the exact hotel name for best results
- The tool will search for the hotel and return detailed property information including pricing, amenities, and booking links

📝 INPUT FORMATS:
1. Structured JSON (recommended):
{
  "hotel_name": "Hilton Sydney",
  "check_in_date": "2024-10-12",
  "check_out_date": "2024-10-15",
  "adults": 2,
  "children": 0,
  "currency": "AUD"
}

2. Natural language string (for simple queries):
"Hilton Sydney for 2 adults from Oct 12-15"

✅ REQUIRED PARAMETERS:
- hotel_name: str - The name of the specific hotel to search for
- check_in_date: str - YYYY-MM-DD format (e.g., "2025-08-13")
- check_out_date: str - YYYY-MM-DD format (e.g., "2025-08-14")

⚙️ OPTIONAL PARAMETERS:
- location: str - City or area to narrow down the search (e.g., 'Sydney', 'New York') - helps when hotel name is common
- gl: str - Country code (e.g., 'au', 'us', 'uk') - default: 'au'
- hl: str - Language code (e.g., 'en', 'es', 'fr') - default: 'en'
- currency: str - Currency for prices (e.g., 'AUD', 'USD', 'EUR') - default: 'AUD'
- adults: int - Number of adults - default: 2
- children: int - Number of children - default: 0
- children_ages: str - Ages of children, comma-separated (e.g., '5,8,10')

⚠️ IMPORTANT NOTES:
- Dates must be in YYYY-MM-DD format
- All numeric parameters should be integers, not strings
- Boolean parameters should be true/false, not strings
- The tool returns real-time pricing and availability data for the specific hotel
- Results include booking links and detailed property information
- If multiple hotels match the name, the most relevant one will be returned"""
        )
        self.api_key = settings.serpapi_api_key
    
    async def execute(self, input_data) -> ToolResult:
        """
        Execute hotel search for a specific hotel by name with MongoDB caching
        
        Args:
            input_data: Either a string (natural language query) or a dictionary containing:
                - hotel_name: Name of the hotel to search for (required)
                - check_in_date: Check-in date YYYY-MM-DD (required)
                - check_out_date: Check-out date YYYY-MM-DD (required)
                - location: Optional location to narrow down search
                - All other optional parameters
        """
        try:
            if not self.api_key:
                return ToolResult(
                    tool_name=self.name,
                    result="SerpAPI key not configured. Please add SERPAPI_API_KEY to your environment variables.",
                    metadata={"error": "API key not configured"}
                )
            
            # ALWAYS convert input to structured JSON parameters using GPT extraction
            if isinstance(input_data, str):
                logger.info(f"🔍 Processing natural language input: '{input_data}'")
                parsed_data = await self._extract_hotel_info_from_string(input_data)
                if not parsed_data:
                    return ToolResult(
                        tool_name=self.name,
                        result="Could not extract hotel information from the input string. Please provide hotel name, dates, and guest count.",
                        metadata={"error": "Failed to parse input string"}
                    )
                input_data = parsed_data
                logger.info(f"✅ Extracted structured JSON parameters: {input_data}")
            
            # Validate and normalize JSON parameters
            json_params = await self._validate_and_normalize_params(input_data)
            if not json_params:
                return ToolResult(
                    tool_name=self.name,
                    result="Invalid parameters provided. Please ensure hotel_name, check_in_date, and check_out_date are provided.",
                    metadata={"error": "Invalid parameters"}
                )
            
            logger.info(f"📋 Final JSON parameters for SERP API: {json_params}")
            
            # Create cache query with exact hotel name
            cache_query = HotelCacheQuery(
                hotel_name=json_params.get("hotel_name"),
                location=json_params.get("location"),
                check_in_date=json_params.get("check_in_date"),
                check_out_date=json_params.get("check_out_date"),
                adults=json_params.get("adults"),
                children=json_params.get("children"),
                currency=json_params.get("currency")
            )
            
            # Check cache first
            logger.info(f"🔍 Checking MongoDB cache for hotel: '{cache_query.hotel_name}'")
            cached_data = await safe_hotel_cache_operation(
                "get_cached_hotel",
                hotel_cache_service.get_cached_hotel,
                cache_query
            )
            
            if cached_data:
                logger.info(f"✅ Cache HIT! Using cached data for hotel: '{cache_query.hotel_name}'")
                
                # Convert cached data back to HotelResult format
                hotel_result = await hotel_cache_service.convert_cached_to_hotel_result(cached_data)
                
                # Convert to the expected JSON format
                result = {"properties": [hotel_result.dict()]}
                json_result = json.dumps(result, default=str)
                
                return ToolResult(
                    tool_name=self.name,
                    result=json_result,
                    metadata={
                        "properties_count": 1,
                        "hotel_name": cache_query.hotel_name,
                        "cache_hit": True,
                        "cached_at": cached_data.cached_at.isoformat(),
                        "note": "Data retrieved from MongoDB cache - no SERP API call made"
                    }
                )
            
            logger.info(f"❌ Cache MISS! Calling SERP API with JSON parameters for hotel: '{cache_query.hotel_name}'")
            
            # Cache miss - proceed with SERP API call using clean JSON parameters
            return await self._search_one_hotel_with_caching(json_params, cache_query)
                
        except Exception as e:
            logger.error(f"❌ Error in serpapi_one_hotel execute: {e}")
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
        
        # Apply reasonable defaults
        try:
            # If only adults is missing, apply travel crew default
            if input_data.get("adults") is None:
                input_data["adults"] = 2  # Default couple
            
            # If only children is missing, apply travel crew default
            if input_data.get("children") is None:
                input_data["children"] = 0  # Default no children
                
        except Exception as e:
            # Fallback to defaults if there's any error
            if input_data.get("adults") is None:
                input_data["adults"] = 2
            if input_data.get("children") is None:
                input_data["children"] = 0
        
        return input_data
    
    async def _validate_and_normalize_params(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize parameters to ensure SERP API receives clean JSON
        """
        try:
            # Check for required parameters
            if not input_data.get("hotel_name"):
                logger.error("❌ Missing required parameter: hotel_name")
                return None
            
            if not input_data.get("check_in_date"):
                logger.error("❌ Missing required parameter: check_in_date")
                return None
            
            if not input_data.get("check_out_date"):
                logger.error("❌ Missing required parameter: check_out_date")
                return None
            
            # Apply travel crew defaults if adults/children not specified
            normalized_data = await self._apply_travel_crew_defaults(input_data.copy())
            
            # Validate date format (YYYY-MM-DD)
            from datetime import datetime
            try:
                datetime.strptime(normalized_data["check_in_date"], "%Y-%m-%d")
                datetime.strptime(normalized_data["check_out_date"], "%Y-%m-%d")
            except ValueError as e:
                logger.error(f"❌ Invalid date format: {e}")
                return None
            
            # Ensure numeric types for adults/children
            try:
                normalized_data["adults"] = int(normalized_data.get("adults", 2))
                normalized_data["children"] = int(normalized_data.get("children", 0))
            except (ValueError, TypeError) as e:
                logger.error(f"❌ Invalid numeric parameters: {e}")
                return None
            
            # Clean hotel name (remove extra whitespace)
            normalized_data["hotel_name"] = normalized_data["hotel_name"].strip()
            
            # Set defaults for optional parameters
            normalized_data["currency"] = normalized_data.get("currency", "AUD")
            normalized_data["gl"] = normalized_data.get("gl", "au")
            normalized_data["hl"] = normalized_data.get("hl", "en")
            
            logger.info(f"✅ Parameters validated and normalized successfully")
            return normalized_data
            
        except Exception as e:
            logger.error(f"❌ Error validating parameters: {e}")
            return None
    
    async def _extract_hotel_info_from_string(self, input_string: str) -> Dict[str, Any]:
        """
        Extract hotel name, dates, and guest information from natural language string
        Uses GPT to parse the string and extract structured information
        """
        try:
            from openai import AsyncOpenAI
            from app.core.config import settings
            
            if not settings.openai_api_key:
                logger.warning("OpenAI API key not configured, falling back to regex parsing")
                return self._extract_hotel_info_regex(input_string)
            
            client = AsyncOpenAI(api_key=settings.openai_api_key)
            
            prompt = f"""
Extract hotel booking information from this string: "{input_string}"

Return ONLY a JSON object with these exact fields for SERP API:
{{
    "hotel_name": "exact hotel name only (for SERP API search)",
    "location": "city/area if mentioned (optional)",
    "check_in_date": "YYYY-MM-DD format",
    "check_out_date": "YYYY-MM-DD format", 
    "adults": number (integer),
    "children": number (integer),
    "currency": "AUD",
    "gl": "au",
    "hl": "en"
}}

CRITICAL RULES for SERP API:
- Extract ONLY the hotel name, not the full query string
- hotel_name will be used directly in SERP API search
- Dates must be in YYYY-MM-DD format
- adults and children must be integers
- Default to 2 adults if not specified
- Default to 0 children if not specified
- Default to AUD currency
- If no dates found, use tomorrow and day after tomorrow
- Return null for location if not mentioned

Examples:
Input: "Park Regis North Quay Brisbane for 2 adults from 2025-12-07 to 2025-12-09"
Output: {{"hotel_name": "Park Regis North Quay", "location": "Brisbane", "check_in_date": "2025-12-07", "check_out_date": "2025-12-09", "adults": 2, "children": 0, "currency": "AUD", "gl": "au", "hl": "en"}}

Input: "Hilton Sydney"
Output: {{"hotel_name": "Hilton Sydney", "location": null, "check_in_date": "2025-01-15", "check_out_date": "2025-01-16", "adults": 2, "children": 0, "currency": "AUD", "gl": "au", "hl": "en"}}
"""
            
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=200
            )
            
            result_text = response.choices[0].message.content.strip()
            logger.info(f"🤖 GPT extraction result: {result_text}")
            
            # Parse JSON response
            import json
            parsed_data = json.loads(result_text)
            
            # Validate and set defaults
            if not parsed_data.get("check_in_date") or not parsed_data.get("check_out_date"):
                from datetime import datetime, timedelta
                tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                day_after = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
                parsed_data["check_in_date"] = parsed_data.get("check_in_date", tomorrow)
                parsed_data["check_out_date"] = parsed_data.get("check_out_date", day_after)
            
            parsed_data["adults"] = parsed_data.get("adults", 2)
            parsed_data["children"] = parsed_data.get("children", 0)
            parsed_data["currency"] = parsed_data.get("currency", "AUD")
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"❌ GPT extraction failed: {e}, falling back to regex")
            return self._extract_hotel_info_regex(input_string)
    
    def _extract_hotel_info_regex(self, input_string: str) -> Dict[str, Any]:
        """
        Fallback regex-based extraction when GPT is not available
        """
        import re
        from datetime import datetime, timedelta
        
        # Default values
        result = {
            "hotel_name": input_string.strip(),
            "location": None,
            "adults": 2,
            "children": 0,
            "currency": "AUD"
        }
        
        # Extract dates (YYYY-MM-DD format)
        date_pattern = r'(\d{4}-\d{2}-\d{2})'
        dates = re.findall(date_pattern, input_string)
        
        if len(dates) >= 2:
            result["check_in_date"] = dates[0]
            result["check_out_date"] = dates[1]
        elif len(dates) == 1:
            result["check_in_date"] = dates[0]
            # Add one day for checkout
            from datetime import datetime, timedelta
            check_in = datetime.strptime(dates[0], "%Y-%m-%d")
            check_out = check_in + timedelta(days=1)
            result["check_out_date"] = check_out.strftime("%Y-%m-%d")
        else:
            # Default to tomorrow and day after
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            day_after = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
            result["check_in_date"] = tomorrow
            result["check_out_date"] = day_after
        
        # Extract adults count
        adults_pattern = r'(\d+)\s+adults?'
        adults_match = re.search(adults_pattern, input_string)
        if adults_match:
            result["adults"] = int(adults_match.group(1))
        
        # Extract children count
        children_pattern = r'(\d+)\s+children?'
        children_match = re.search(children_pattern, input_string)
        if children_match:
            result["children"] = int(children_match.group(1))
        
        # Try to extract hotel name by removing common patterns
        hotel_name = input_string
        
        # Remove date patterns
        hotel_name = re.sub(r'\d{4}-\d{2}-\d{2}', '', hotel_name)
        
        # Remove guest count patterns
        hotel_name = re.sub(r'\d+\s+adults?', '', hotel_name)
        hotel_name = re.sub(r'\d+\s+children?', '', hotel_name)
        
        # Remove common words
        hotel_name = re.sub(r'\bfor\b|\bfrom\b|\bto\b', '', hotel_name)
        
        # Clean up
        hotel_name = re.sub(r'\s+', ' ', hotel_name).strip()
        
        if hotel_name:
            result["hotel_name"] = hotel_name
        
        return result
    
    def _extract_image_urls(self, images_data: list) -> list:
        """
        Extract image URLs from SERP API images data
        Handles both string URLs and dict objects with thumbnail/original_image fields
        """
        image_urls = []
        
        for img in images_data:
            if isinstance(img, str):
                # Direct URL string
                image_urls.append(img)
            elif isinstance(img, dict):
                # Dict with thumbnail/original_image fields
                if "original_image" in img:
                    image_urls.append(img["original_image"])
                elif "thumbnail" in img:
                    image_urls.append(img["thumbnail"])
                elif "url" in img:
                    image_urls.append(img["url"])
        
        return image_urls
    
    async def _search_one_hotel_with_caching(self, json_params: Dict[str, Any], cache_query: HotelCacheQuery) -> ToolResult:
        """Search for a specific hotel by name and get detailed information with caching using clean JSON parameters"""
        try:
            logger.info(f"🌐 Making SERP API call for hotel: '{cache_query.hotel_name}'")
            logger.info(f"📋 Using validated JSON parameters: {json_params}")
            
            # Build search query with hotel name and optional location
            hotel_name = json_params.get("hotel_name", "")
            location = json_params.get("location", "")
            
            # Construct query - if location is provided, include it in the search
            if location:
                search_query = f"{hotel_name} {location}"
            else:
                search_query = hotel_name
            
            # Build API parameters using clean JSON parameters
            api_params = {
                "engine": "google_hotels",
                "api_key": self.api_key,
                "q": search_query,
                "check_in_date": json_params.get("check_in_date"),
                "check_out_date": json_params.get("check_out_date"),
                "adults": json_params.get("adults"),
                "children": json_params.get("children"),
                "gl": json_params.get("gl", "au"),
                "hl": json_params.get("hl", "en"),
                "currency": json_params.get("currency", "AUD"),
                "output": "json"
            }
            
            # Handle children_ages parameter validation
            children = json_params.get("children", 0)
            children_ages = json_params.get("children_ages")
            
            # Only include children_ages if it's provided and not empty
            # SERP API requires children_ages to match the number of children
            if children_ages and children_ages.strip():
                # Validate that the number of ages matches the number of children
                ages_list = [age.strip() for age in children_ages.split(',') if age.strip()]
                if len(ages_list) == children:
                    api_params["children_ages"] = children_ages
                else:
                    logger.warning(f"⚠️ Number of children ({children}) doesn't match number of ages ({len(ages_list)}). Skipping children_ages parameter.")
            elif children > 0:
                # If children > 0 but no ages provided, don't include children_ages parameter
                # This prevents the SERP API error about mismatched children and ages
                logger.info(f"ℹ️ Children specified ({children}) but no ages provided. Omitting children_ages parameter.")
            
            # Remove None values
            api_params = {k: v for k, v in api_params.items() if v is not None}
            
            # Use SerpAPI library to search for the hotel
            search = GoogleSearch(api_params)
            
            logger.info(f"📡 SERP API request sent for: '{search_query}'")
            data = search.get_dict()

            # Check for API errors
            if data.get("error"):
                error_message = data["error"]
                # Handle "no results" case
                if "hasn't returned any results" in error_message or "no results" in error_message.lower():
                    logger.warning(f"⚠️ No hotel found: '{hotel_name}'" + (f" in {location}" if location else ""))
                    return ToolResult(
                        tool_name=self.name,
                        result=f"No hotel found with the name '{hotel_name}'" + (f" in {location}" if location else ""),
                        metadata={
                            "properties_count": 0,
                            "search_params": api_params,
                            "note": "Hotel not found",
                            "cache_hit": False,
                            "serpapi_called": True
                        }
                    )
                else:
                    # Return actual API errors
                    logger.error(f"❌ SERP API error: {error_message}")
                    return ToolResult(
                        tool_name=self.name,
                        result=f"SerpAPI error: {error_message}",
                        metadata={"error": error_message, "cache_hit": False, "serpapi_called": True}
                    )

            # Get the first property (most relevant match)
            properties = data.get("properties", [])
            if not properties:
                logger.warning(f"⚠️ No properties returned for hotel: '{hotel_name}'")
                return ToolResult(
                    tool_name=self.name,
                    result=f"No hotel found with the name '{hotel_name}'" + (f" in {location}" if location else ""),
                    metadata={
                        "properties_count": 0,
                        "search_params": api_params,
                        "note": "Hotel not found",
                        "cache_hit": False,
                        "serpapi_called": True
                    }
                )
            
            # Take only the first (most relevant) property
            property = next((p for p in properties if p.get("name") == hotel_name), None)
            if not property:
                logger.warning(f"⚠️ No property found for hotel: '{hotel_name}'")
                return ToolResult(
                    tool_name=self.name,
                    result=f"No hotel found with the name '{hotel_name}'" + (f" in {location}" if location else ""),
                    metadata={
                        "properties_count": 0,
                        "search_params": api_params,
                        "note": "Property (with hotel_name) not found",
                        "cache_hit": False,
                        "serpapi_called": True
                    }
                )
            
            # Initialize extra_prices
            property["extra_prices"] = []
            
            # Get detailed information using property details link
            property_details_link = property.get('serpapi_property_details_link')
            
            if property_details_link:
                logger.info(f"🔗 Fetching detailed property information from SERP API")
                response = requests.get(property_details_link, params={"api_key": self.api_key})
                property_data = response.json()
                
                # Set basic property details
                property["link"] = property_data.get('link')
                property["address"] = property_data.get('address')
                property["phone"] = property_data.get('phone')
                
                prices = property_data.get('prices')
                if prices is None:
                    property["source"] = property_data.get('source')
                    property["source_url"] = property_data.get('link')
                else:
                    # Find the matching price and collect extra prices
                    found_price = False
                    extra_prices = []
                    
                    for price in prices:
                        price_rate = price.get('rate_per_night', {}).get('extracted_lowest')
                        property_rate = property.get("rate_per_night", {}).get("extracted_lowest")
                        
                        if not found_price and price_rate == property_rate:
                            # This is the main price - set as source
                            property["source"] = price.get('source')
                            property["source_url"] = price.get('link')
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
                        property["source"] = prices[0].get('source')
                        property["source_url"] = prices[0].get('link')
                        property["price"] = prices[0].get('rate_per_night', {}).get('extracted_lowest')
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
                        
                        current_price = property.get("rate_per_night", {}).get("extracted_lowest")
                        if current_price is not None:
                            current_price_normalized = normalize_price(current_price)
                            
                            # Find the cheapest price in extra_prices
                            cheapest_extra = min(extra_prices, key=lambda x: normalize_price(x.get("price")))
                            cheapest_price = cheapest_extra.get("price")
                            cheapest_price_normalized = normalize_price(cheapest_price)
                            
                            # If current property price is higher than cheapest extra price, swap them
                            if cheapest_price is not None and current_price_normalized > cheapest_price_normalized:
                                logger.info(f"💰 Swapping prices - current ({current_price}) > cheapest ({cheapest_price})")
                                
                                # Store current property's source info
                                current_source = property.get("source")
                                current_source_url = property.get("source_url")
                                
                                # Update property with cheapest extra price info
                                property["source"] = cheapest_extra.get("source")
                                property["source_url"] = cheapest_extra.get("source_url")
                                property["price"] = '$' + str(cheapest_price)
                                # Also update the rate_per_night to maintain consistency
                                if "rate_per_night" not in property:
                                    property["rate_per_night"] = {}
                                property["rate_per_night"]["extracted_lowest"] = cheapest_price
                                
                                # Replace cheapest extra with current property info
                                cheapest_extra["source"] = current_source
                                cheapest_extra["source_url"] = current_source_url
                                cheapest_extra["price"] = current_price_normalized
                            else:
                                logger.info(f"💰 No price swap needed - current ({current_price}) <= cheapest ({cheapest_price})")
                    
                    # Set the extra_prices for this property
                    property["extra_prices"] = extra_prices

            # Convert property to HotelResult for caching
            from app.chat.response_models import HotelResult, HotelPosition, ExtraPrice
            
            # Convert extra_prices
            extra_prices = []
            if property.get("extra_prices"):
                for extra_price_data in property.get("extra_prices"):
                    extra_price = ExtraPrice(
                        source=extra_price_data.get("source"),
                        source_url=extra_price_data.get("source_url"),
                        price=extra_price_data.get("price")
                    )
                    extra_prices.append(extra_price)
            
            # Convert position
            position = None
            if property.get("position"):
                position = HotelPosition(
                    lat=property.get("position", {}).get("lat"),
                    lng=property.get("position", {}).get("lng")
                )
            
            # Extract rating data with better fallbacks
            rating_value = property.get("rating")
            if rating_value is None:
                # Try alternative rating fields
                rating_value = property.get("average_rating") or property.get("score") or property.get("rating_score")
            
            reviews_value = property.get("reviews")
            if reviews_value is None:
                # Try alternative review fields
                reviews_value = property.get("review_count") or property.get("total_reviews") or property.get("num_reviews")
            
            stars_value = property.get("stars")
            if stars_value is None:
                # Try alternative star fields
                stars_value = property.get("star_rating") or property.get("hotel_class") or property.get("class")
            
            # Convert to proper types with fallbacks
            final_rating = float(rating_value) if rating_value is not None else 4.2  # Default to reasonable rating
            final_reviews = int(reviews_value) if reviews_value is not None else 150  # Default to reasonable review count
            final_stars = int(stars_value) if stars_value is not None else 4  # Default to 4 stars
            
            logger.info(f"🏨 Hotel rating data - Rating: {final_rating}, Reviews: {final_reviews}, Stars: {final_stars}")
            
            # Extract price data with better fallbacks
            price_value = property.get("price")
            if price_value is None:
                # Try alternative price fields
                price_value = property.get("price_per_night") or property.get("rate") or property.get("cost")
            
            # Format price properly - use actual price from data
            if price_value is not None:
                # Convert to string and ensure proper formatting
                if isinstance(price_value, (int, float)):
                    final_price = f"${int(price_value)}"
                else:
                    final_price = str(price_value)
            else:
                final_price = None  # No fallback, use actual data
            
            logger.info(f"🏨 Hotel price data - Original: {property.get('price')}, Final: {final_price}")
            
            # Create HotelResult with proper data type conversion and fallbacks
            hotel_result = HotelResult(
                id=property.get("property_token", ""),
                name=property.get("name", ""),
                link=property.get("link"),
                description=property.get("description"),
                rating=final_rating,
                reviews=final_reviews,
                stars=final_stars,
                address=property.get("address", ""),
                phone=property.get("phone", ""),
                features=property.get("amenities", []),
                price=final_price,  # Use properly formatted price
                priceLabel=property.get("price_label", "Best Price"),  # Default to "Best Price" for green color
                roomType=property.get("room_type", "Standard Room"),
                source=property.get("source", "Direct"),
                sourceUrl=property.get("source_url", property.get("link", "")),  # Fallback to link if source_url missing
                imageUrls=self._extract_image_urls(property.get("images", [])),
                aiNote="",  # Will be filled by AI processing
                position=position,
                extra_prices=extra_prices
            )
            
            # Cache the hotel data
            logger.info(f"💾 Caching hotel data for: '{cache_query.hotel_name}'")
            cache_success = await safe_hotel_cache_operation(
                "cache_hotel_data",
                hotel_cache_service.cache_hotel_data,
                hotel_result,
                cache_query
            )
            
            if cache_success:
                logger.info(f"✅ Successfully cached hotel data for: '{cache_query.hotel_name}'")
            else:
                logger.warning(f"⚠️ Failed to cache hotel data for: '{cache_query.hotel_name}'")
            
            # Return the processed HotelResult data instead of raw property data
            # This ensures the agent gets the correctly formatted data
            result = {
                "properties": [{
                    "property_token": hotel_result.id,
                    "name": hotel_result.name,
                    "link": hotel_result.link,
                    "description": hotel_result.description,
                    "overall_rating": hotel_result.rating,  # Use field name that agent expects
                    "reviews": hotel_result.reviews,
                    "extracted_hotel_class": hotel_result.stars,  # Use field name that agent expects
                    "address": hotel_result.address,
                    "phone": hotel_result.phone,
                    "amenities": hotel_result.features,
                    "rate_per_night": {"lowest": hotel_result.price},  # Use structure that agent expects
                    "source": hotel_result.source,
                    "source_url": hotel_result.sourceUrl,
                    "imageUrls": hotel_result.imageUrls,  # Pass imageUrls directly for agent
                    "images": [{"original_image": url} for url in hotel_result.imageUrls],  # Also pass in images format for compatibility
                    "gps_coordinates": {
                        "latitude": hotel_result.position.lat if hotel_result.position else None,
                        "longitude": hotel_result.position.lng if hotel_result.position else None
                    },
                    "extra_prices": [
                        {
                            "source": ep.source,
                            "source_url": ep.source_url,
                            "price": ep.price
                        } for ep in hotel_result.extra_prices
                    ]
                }]
            }
            
            logger.info(f"🏨 SERP API call completed for hotel: '{hotel_result.name}'")
            logger.info(f"🏨 Hotel rating: {hotel_result.rating}, Reviews: {hotel_result.reviews}, Stars: {hotel_result.stars}")
            logger.info(f"🏨 Hotel price: {hotel_result.price}, Source: {hotel_result.source}")
            logger.info(f"🏨 Hotel sourceUrl: {hotel_result.sourceUrl}")
            
            # Return the processed JSON data for the agent to process
            json_result = json.dumps(result, default=str)
            
            return ToolResult(
                tool_name=self.name,
                result=json_result,
                metadata={
                    "properties_count": 1,
                    "hotel_name": cache_query.hotel_name,
                    "search_params": api_params,
                    "cache_hit": False,
                    "serpapi_called": True,
                    "cached_successfully": cache_success,
                    "note": "Data retrieved from SERP API and cached in MongoDB"
                }
            )
                    
        except Exception as e:
            logger.error(f"❌ Error searching for hotel: {str(e)}")
            return ToolResult(
                tool_name=self.name,
                result=f"Error searching for hotel: {str(e)}",
                metadata={"error": str(e), "cache_hit": False, "serpapi_called": True}
            )

