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
from app.chat.response_models import HotelResult, HotelPosition, ExtraPrice

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
    
    def _create_langchain_function(self):
        """Create a LangChain-compatible function wrapper"""
        from langchain.tools import StructuredTool
        
        def langchain_wrapper(hotel_name: str, check_in_date: str, check_out_date: str, 
                             location: str = None, gl: str = "au", hl: str = "en", 
                             currency: str = "AUD", adults: int = 2, children: int = 0) -> str:
            """LangChain-compatible wrapper for the tool"""
            import asyncio
            
            input_data = {
                "hotel_name": hotel_name,
                "check_in_date": check_in_date,
                "check_out_date": check_out_date,
                "location": location,
                "gl": gl,
                "hl": hl,
                "currency": currency,
                "adults": adults,
                "children": children
            }
            
            # Run the async execute method in a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.execute(input_data))
                return result.result
            finally:
                loop.close()
        
        return StructuredTool.from_function(
            func=langchain_wrapper,
            name=self.name,
            description=self.description
        )
    
    async def execute(self, input_data: Dict[str, Any]) -> ToolResult:
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
            
            # Handle structured input from LangChain tool calling system
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
            elif isinstance(input_data, dict):
                logger.info(f"🔍 Processing structured input: {input_data}")
                # Input is already structured, use as-is
            else:
                return ToolResult(
                    tool_name=self.name,
                    result="Invalid input format. Expected dictionary with hotel_name, check_in_date, check_out_date.",
                    metadata={"error": "Invalid input format"}
                )
            
            # Validate and normalize JSON parameters
            json_params = await self._validate_and_normalize_params(input_data)
            if not json_params:
                return ToolResult(
                    tool_name=self.name,
                    result="Invalid parameters provided. Please ensure hotel_name, check_in_date, and check_out_date are provided.",
                    metadata={"error": "Invalid parameters"}
                )
            
            logger.info(f"📋 Final JSON parameters for SERP API: {json_params}")
            
            # # Create cache query with exact hotel name
            cache_query = HotelCacheQuery(
                hotel_name=json_params.get("hotel_name"),
                location=json_params.get("location"),
                check_in_date=json_params.get("check_in_date"),
                check_out_date=json_params.get("check_out_date"),
                adults=json_params.get("adults"),
                children=json_params.get("children"),
                currency=json_params.get("currency")
            )
            
            # # Check cache first
            # logger.info(f"🔍 Checking MongoDB cache for hotel: '{cache_query.hotel_name}'")
            # cached_data = await safe_hotel_cache_operation(
            #     "get_cached_hotel",
            #     hotel_cache_service.get_cached_hotel,
            #     cache_query
            # )
            
            # if cached_data:
            #     logger.info(f"✅ Cache HIT! Using cached data for hotel: '{cache_query.hotel_name}'")
                
            #     # Convert cached data back to HotelResult format
            #     hotel_result = await hotel_cache_service.convert_cached_to_hotel_result(cached_data)
                
            #     # Convert to the expected JSON format
            #     result = {"properties": [hotel_result.dict()]}
            #     json_result = json.dumps(result, default=str)
                
            #     return ToolResult(
            #         tool_name=self.name,
            #         result=json_result,
            #         metadata={
            #             "properties_count": 1,
            #             "hotel_name": cache_query.hotel_name,
            #             "cache_hit": True,
            #             "cached_at": cached_data.cached_at.isoformat(),
            #             "note": "Data retrieved from MongoDB cache - no SERP API call made"
            #         }
            #     )
            
            # logger.info(f"❌ Cache MISS! Calling SERP API with JSON parameters for hotel: '{cache_query.hotel_name}'")
            
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
- remove normal words related to hotel, e.g., remove "hotel" at the end of name
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
        
        # Remove currency-related strings
        hotel_name = re.sub(r'\bcurrency\s+\w+\b', '', hotel_name, flags=re.IGNORECASE)
        
        # Remove trailing commas
        hotel_name = re.sub(r',\s*$', '', hotel_name)
        
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
                if "thumbnail" in img:
                    image_urls.append(img["thumbnail"])
                elif "original_image" in img:
                    image_urls.append(img["original_image"])
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
            if properties:
                property = next((p for p in properties if p.get("name") == hotel_name), None)
                if not property:
                    # No exact match found, calculate similarity for all properties
                    import difflib
                    best_match = None
                    best_similarity = 0
                    
                    for prop in properties:
                        prop_name = prop.get("name", "")
                        if prop_name:
                            # Calculate similarity ratio (0.0 to 1.0)
                            similarity = difflib.SequenceMatcher(None, hotel_name.lower(), prop_name.lower()).ratio()
                            
                            # If similarity is over 90% (0.9), use this property
                            if similarity > 0.9 and similarity > best_similarity:
                                best_similarity = similarity
                                best_match = prop
                                logger.info(f"🎯 Found high similarity match: '{prop_name}' (similarity: {similarity:.2%})")
                    
                    if best_match:
                        property = best_match
                        logger.info(f"✅ Using similarity match: '{property.get('name')}' with {best_similarity:.2%} similarity")
                    else:
                        logger.warning(f"⚠️ No properties found with >90% similarity to '{hotel_name}'")
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
                    logger.info(f"✅ Found exact match: '{property.get('name')}'")
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
                            sorted_prices = sorted(prices, key=lambda x: x.get("rate_per_night", {}).get("extracted_lowest"))
                            
                            # Check if we have any prices
                            if sorted_prices:
                                property["source"] = sorted_prices[0].get("source")
                                property["source_url"] = sorted_prices[0].get("link")
                                property["price"] = sorted_prices[0].get("rate_per_night", {}).get("extracted_lowest")
                                property["extraced_lowest"] = sorted_prices[0].get("rate_per_night", {}).get("extracted_lowest")
                                property["rate_per_night"] = sorted_prices[0].get("rate_per_night", {})
                                extra_prices = []
                                for price in sorted_prices[1:]:
                                    extra_price = {
                                        "source": price.get("source"),
                                        "source_url": price.get("link"),
                                        "price": price.get("rate_per_night", {}).get("extracted_lowest")
                                    }
                                    # extra_price = ExtraPrice(
                                    #     source=price.get("source"),
                                    #     source_url=price.get("link"),
                                    #     price=price.get("rate_per_night", {}).get("extracted_lowest")
                                    # )
                                    extra_prices.append(extra_price)
                                    if len(extra_prices) >= 2:
                                        break
                                # Set the extra_prices for this property
                                property["extra_prices"] = extra_prices
                            else:
                                # No prices available, set defaults
                                property["source"] = property_data.get('source')
                                property["source_url"] = property_data.get('link')
                                property["price"] = None
                                property["extraced_lowest"] = None
                                property["rate_per_night"] = {}
                                property["extra_prices"] = []           
            else:
                property = {
                    "type": data.get("type", ""),
                    "name": data.get("name", ""),
                    "link": data.get("link", ""),
                    "address": data.get("address", ""),
                    "phone": data.get("phone", ""),
                    "rating": data.get("rating", None),
                    "reviews": data.get("reviews") if data.get("reviews") else None,
                    "description": data.get("description", ""),
                    "price": data.get("rate_per_night", {}).get("extracted_lowest"),
                    "rate_per_night": data.get("rate_per_night", {}),
                    "hotel_class": data.get("extracted_hotel_class", None),
                    "images": data.get("images", []),
                    "overall_rating": data.get("overall_rating") if data.get("overall_rating") else None,
                    "amenities": data.get("amenities", []),
                    "excluded_amenities": data.get("excluded_amenities", []),
                    "prices": data.get("prices", []),
                    "gps_coordinates": data.get("gps_coordinates", {}),
                    "position": data.get("gps_coordinates", {}),
                }
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
                prices = property.get('prices')
                if prices is None:
                    property["source"] = data.get('source')
                    property["source_url"] = data.get('link')
                else:
                    # Find the matching price and collect extra prices
                    sorted_prices = sorted(prices, key=lambda x: x.get("rate_per_night", {}).get("extracted_lowest"))
                    
                    # Check if we have any prices
                    if sorted_prices:
                        property["source"] = sorted_prices[0].get("source")
                        property["source_url"] = sorted_prices[0].get("link")
                        property["price"] = sorted_prices[0].get("rate_per_night", {}).get("extracted_lowest")
                        property["extraced_lowest"] = sorted_prices[0].get("rate_per_night", {}).get("extracted_lowest")
                        property["rate_per_night"] = sorted_prices[0].get("rate_per_night", {})
                        extra_prices = []
                        for price in sorted_prices[1:]:
                            extra_price = {
                                "source": price.get("source"),
                                "source_url": price.get("link"),
                                "price": price.get("rate_per_night", {}).get("extracted_lowest")
                            }
                            # extra_price = ExtraPrice(
                            #     source=price.get("source"),
                            #     source_url=price.get("link"),
                            #     price=price.get("rate_per_night", {}).get("extracted_lowest")
                            # )
                            extra_prices.append(extra_price)
                            if len(extra_prices) >= 3:
                                break
                        # Set the extra_prices for this property
                        property["extra_prices"] = extra_prices
                    else:
                        # No prices available, set defaults
                        property["source"] = data.get('source')
                        property["source_url"] = data.get('link')
                        property["price"] = None
                        property["extraced_lowest"] = None
                        property["rate_per_night"] = {}
                        property["extra_prices"] = []

                # Convert property to HotelResult for caching
                result = {"properties": [property]}
                
                print(f"=" * 80)
                print(f"🏨 SERPAPI_ONE_HOTEL TOOL - Returning result")
                print(f"🏨 Property name: {property.get('name')}")
                print(f"🏨 Property has link: {property.get('link') is not None}")
                print(f"🏨 Property has images: {len(property.get('images', []))}")
                print(f"🏨 Property has extra_prices: {len(property.get('extra_prices', []))}")
                print(f"=" * 80)
                
                # Return the raw JSON data for the agent to process
                import json
                json_result = json.dumps(result, default=str)
                
                return ToolResult(
                    tool_name=self.name,
                    result=json_result,
                    metadata={
                        "properties_count": 1,
                        "hotel_name": hotel_name,
                        "search_params": api_params
                    }
                )
            
            # Return the processed JSON data for the agent to process
            # json_result = json.dumps(result, default=str)
            
            # return ToolResult(
            #     tool_name=self.name,
            #     result=json_result,
            #     metadata={
            #         "properties_count": 1,
            #         "hotel_name": cache_query.hotel_name,
            #         "search_params": api_params,
            #         "cache_hit": False,
            #         "serpapi_called": True,
            #         "cached_successfully": cache_success,
            #         "note": "Data retrieved from SERP API and cached in MongoDB"
            #     }
            # )
                    
        except Exception as e:
            logger.error(f"❌ Error searching for hotel: {str(e)}")
            return ToolResult(
                tool_name=self.name,
                result=f"Error searching for hotel: {str(e)}",
                metadata={"error": str(e), "cache_hit": False, "serpapi_called": True}
            )

