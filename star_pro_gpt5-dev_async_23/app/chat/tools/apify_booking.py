from typing import Dict, Any
import asyncio
import aiohttp
import json
from app.chat.tools.base import BaseTool
from app.chat.models import ToolResult
from app.core.config import settings

class ApifyBookingTool(BaseTool):
    """Tool for searching hotels using Apify Booking Hotels actor"""
    
    def __init__(self):
        super().__init__(
            name="apify_booking",
            description="""Search for hotels and vacation rentals using Apify Booking Hotels actor.

🎯 USAGE GUIDANCE:
- Always extract dates from user queries and convert to YYYY-MM-DD format
- Set appropriate currency based on location (AUD for Australia, USD for US, etc.)
- Use location as a list of strings for better search results
- The tool performs a two-step process: run actor and get results

📝 INPUT FORMATS:
1. Structured JSON (recommended):
{
  "check_in": "2025-10-12",
  "check_out": "2025-10-14", 
  "location": ["gold coast"],
  "adults": 2,
  "rooms": 1,
  "currency": "AUD",
  "limit": 5
}

2. Natural language string (for simple queries):
"Hotels in Gold Coast for 2 adults from Oct 12-14"

✅ REQUIRED PARAMETERS:
- check_in: str - Check-in date in YYYY-MM-DD format (Required)
- check_out: str - Check-out date in YYYY-MM-DD format (Required)
- location: list - List of location strings (e.g., ["gold coast", "sydney"])

⚙️ OPTIONAL PARAMETERS:
- adults: int - Number of adults (default: 2)
- rooms: int - Number of rooms (default: 1)
- currency: str - Currency code (default: "AUD")
- language: str - Language code (default: "en-gb")
- limit: int - Maximum results to return (default: 5)
- sort: str - Sort order: "popular", "price", "rating" (default: "popular")
- entire_place: bool - Search for entire places only (default: false)
- flexdate: str - Flexible date range in days (default: "7")
- includes.all: bool - Include all details (default: true)
- includes.description: bool - Include descriptions (default: true)
- includes.facilities: bool - Include facilities (default: true)
- includes.gallery: bool - Include gallery images (default: true)
- includes.policies: bool - Include policies (default: true)
- includes.rooms: bool - Include room details (default: true)
- includes.surroundings: bool - Include surroundings info (default: true)
- health_safety: bool - Include health & safety info (default: false)
- sustainable: bool - Include sustainability info (default: false)
- dev_dataset_clear: bool - Clear dataset before run (default: false)
- dev_no_strip: bool - Don't strip results (default: false)

⚠️ IMPORTANT NOTES:
- Dates must be in YYYY-MM-DD format
- Location should be a list of strings for better search accuracy
- The tool performs two API calls: first to run the actor, then to get results
- Results include detailed hotel information with pricing and availability
- Processing may take 30-60 seconds as it scrapes real booking data"""
        )
        self.api_token = settings.apify_token
        self.run_sync_url = "https://api.apify.com/v2/acts/XqyIZxHDZ5OfyKy6z/run-sync"
        self.dataset_url = "https://api.apify.com/v2/acts/XqyIZxHDZ5OfyKy6z/runs/last/dataset/items"
    
    async def execute(self, input_data) -> ToolResult:
        """
        Execute hotel search using Apify Booking Hotels actor
        
        Args:
            input_data: Either a string (natural language query) or a dictionary containing:
                - check_in: Check-in date YYYY-MM-DD (required)
                - check_out: Check-out date YYYY-MM-DD (required)
                - location: List of location strings (required)
                - All other optional parameters
        """
        try:
            if not self.api_token:
                return ToolResult(
                    tool_name=self.name,
                    result="Apify token not configured. Please add APIFY_TOKEN to your environment variables.",
                    metadata={"error": "API token not configured"}
                )
            
            # Handle string input (natural language query)
            if isinstance(input_data, str):
                from datetime import datetime, timedelta
                tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                day_after = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
                
                # Try to extract location from the query string
                location = ["gold coast"]  # Default location
                if "sydney" in input_data.lower():
                    location = ["sydney"]
                elif "melbourne" in input_data.lower():
                    location = ["melbourne"]
                elif "brisbane" in input_data.lower():
                    location = ["brisbane"]
                elif "perth" in input_data.lower():
                    location = ["perth"]
                elif "adelaide" in input_data.lower():
                    location = ["adelaide"]
                
                input_data = {
                    "check_in": tomorrow,
                    "check_out": day_after,
                    "location": location
                }
            
            # Map parameter names from schema to tool format
            mapped_input = {}
            for key, value in input_data.items():
                if key == "includes_all":
                    mapped_input["includes.all"] = value
                elif key == "includes_description":
                    mapped_input["includes.description"] = value
                elif key == "includes_facilities":
                    mapped_input["includes.facilities"] = value
                elif key == "includes_gallery":
                    mapped_input["includes.gallery"] = value
                elif key == "includes_policies":
                    mapped_input["includes.policies"] = value
                elif key == "includes_rooms":
                    mapped_input["includes.rooms"] = value
                elif key == "includes_surroundings":
                    mapped_input["includes.surroundings"] = value
                else:
                    mapped_input[key] = value
            
            # Check for required parameters
            if not mapped_input.get("check_in"):
                return ToolResult(
                    tool_name=self.name,
                    result="Missing required parameter: 'check_in'",
                    metadata={"error": "Missing check_in parameter"}
                )
            
            if not mapped_input.get("check_out"):
                return ToolResult(
                    tool_name=self.name,
                    result="Missing required parameter: 'check_out'",
                    metadata={"error": "Missing check_out parameter"}
                )
            
            if not mapped_input.get("location"):
                return ToolResult(
                    tool_name=self.name,
                    result="Missing required parameter: 'location'",
                    metadata={"error": "Missing location parameter"}
                )
            
            return await self._search_hotels(mapped_input)
                
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                result=f"Error processing hotel request: {str(e)}",
                metadata={"error": str(e)}
            )
    
    async def _search_hotels(self, input_data: Dict[str, Any]) -> ToolResult:
        """Search for hotels using Apify actor with two-step process"""
        try:
            # Step 1: Prepare parameters for the run-sync API
            run_params = {
                "check_in": input_data.get("check_in"),
                "check_out": input_data.get("check_out"),
                "currency": input_data.get("currency", "AUD"),
                "dev_dataset_clear": input_data.get("dev_dataset_clear", False),
                "dev_no_strip": input_data.get("dev_no_strip", False),
                "entire_place": input_data.get("entire_place", False),
                "flexdate": input_data.get("flexdate", "7"),
                "health_safety": input_data.get("health_safety", False),
                "includes.all": input_data.get("includes.all", True),
                "includes.description": input_data.get("includes.description", True),
                "includes.facilities": input_data.get("includes.facilities", True),
                "includes.fineprints": input_data.get("includes.fineprints", False),
                "includes.gallery": input_data.get("includes.gallery", True),
                "includes.host": input_data.get("includes.host", False),
                "includes.policies": input_data.get("includes.policies", True),
                "includes.rooms": input_data.get("includes.rooms", True),
                "includes.surroundings": input_data.get("includes.surroundings", True),
                "language": input_data.get("language", "en-gb"),
                "limit": input_data.get("limit", 5),
                "location": input_data.get("location"),
                "sort": input_data.get("sort", "popular"),
                "sustainable": input_data.get("sustainable", False),
                "rooms": input_data.get("rooms", 1),
                "adults": input_data.get("adults", 2)
            }
            
            # Step 1: Run the actor
            run_result = await self._run_actor(run_params)
            if not run_result["success"]:
                return ToolResult(
                    tool_name=self.name,
                    result=f"Failed to run Apify actor: {run_result['error']}",
                    metadata={"error": run_result["error"], "step": "run_actor"}
                )
            
            # Step 2: Get the results from the dataset
            dataset_result = await self._get_dataset_items()
            if not dataset_result["success"]:
                return ToolResult(
                    tool_name=self.name,
                    result=f"Failed to get dataset items: {dataset_result['error']}",
                    metadata={"error": dataset_result["error"], "step": "get_dataset"}
                )
            
            # Process and return results
            hotels = dataset_result["data"]
            print(f"DEBUG: hotels = {hotels}")

            # Limit results if specified
            limit = input_data.get("limit", 5)
            if len(hotels) > limit:
                hotels = hotels[:limit]
            
            result = {
                "hotels": hotels,
                "total_found": len(hotels),
                "search_params": run_params
            }
            
            json_result = json.dumps(result, default=str)
            
            return ToolResult(
                tool_name=self.name,
                result=json_result,
                metadata={
                    "hotels_count": len(hotels),
                    "search_params": run_params,
                    "note": "No hotels found" if len(hotels) == 0 else None
                }
            )
                    
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                result=f"Error searching hotels: {str(e)}",
                metadata={"error": str(e)}
            )
    
    def refine_hotel_data(self, data: list) -> list:
        """Refine hotel data to keep only necessary fields"""
        if not isinstance(data, list):
            return data
        
        refined_hotels = []
        
        for hotel in data:
            if not isinstance(hotel, dict):
                continue
                
            # Create refined hotel with only the specified fields
            refined_hotel = {}
            
            # List of fields to keep
            fields_to_keep = [
                'address', 'brands', 'configuration', 'context', 'description',
                'gallery', 'highlights', 'host', 'id', 'isNew', 'languagesSpoken',
                'location', 'meals', 'name', 'photos', 'plus', 'policies',
                'preferred', 'price', 'questions', 'rating', 'restaurants',
                'reviews', 'sustainability', 'type', 'typeId', 'url'
            ]
            
            for field in fields_to_keep:
                if field in hotel:
                    if field == 'gallery' and isinstance(hotel[field], list):
                        # Keep only first 4 items in gallery
                        refined_hotel[field] = hotel[field][:4]
                    else:
                        refined_hotel[field] = hotel[field]
            
            refined_hotels.append(refined_hotel)
        
        return refined_hotels
    
    async def _run_actor(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Step 1: Run the Apify actor"""
        try:
            url = f"{self.run_sync_url}?token={self.api_token}"
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=params, headers=headers) as response:
                    if response.status == 201:
                        # 201 status means the actor was successfully started
                        # We don't need to check the response data, just the status
                        return {"success": True, "status": 201}
                    else:
                        error_text = await response.text()
                        return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
                        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _get_dataset_items(self) -> Dict[str, Any]:
        """Step 2: Get dataset items from the last run"""
        try:
            url = f"{self.dataset_url}?token={self.api_token}"
            
            headers = {
                'Accept': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Refine the hotel data to keep only necessary fields
                        refined_data = self.refine_hotel_data(data)
                        return {"success": True, "data": refined_data}
                    else:
                        error_text = await response.text()
                        return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
                        
        except Exception as e:
            return {"success": False, "error": str(e)}
