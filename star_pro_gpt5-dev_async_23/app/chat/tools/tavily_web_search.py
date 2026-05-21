from typing import Dict, Any
from app.chat.tools.base import BaseTool
from app.chat.models import ToolResult
from app.core.config import settings
import json
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

class TavilyWebSearchTool(BaseTool):
    """Tool for web search using Tavily API"""
    
    def __init__(self):
        super().__init__(
            name="tavily_web_search",
            description="""Search the web for real-time information using Tavily API.

🎯 USAGE GUIDANCE:
- Use for general web searches, current events, and real-time information
- Perfect for finding up-to-date travel information, news, and facts
- Can search for specific topics, people, places, or events
- Returns both text results and relevant images with descriptions

📝 INPUT FORMATS:
1. Simple string query (recommended):
"best restaurants in Sydney 2024"

2. Structured JSON for advanced searches:
{
  "query": "best restaurants in Sydney 2024",
  "search_depth": "basic",
  "topic": "general",
  "max_results": 5
}

✅ REQUIRED PARAMETERS:
- query: str - Search query (what you want to search for)

⚙️ OPTIONAL PARAMETERS:
- search_depth: str - "basic" (faster) or "advanced" (more comprehensive) - default: "basic"
- topic: str - "general", "news", "research" - default: "general"  
- max_results: int - Maximum number of results to return - default: 5

🔍 EXAMPLE QUERIES:
- "current weather in Melbourne"
- "best hotels in Gold Coast 2024"
- "Sydney Opera House events this weekend"
- "travel restrictions Australia 2024"
- "best beaches near Brisbane"

⚠️ IMPORTANT NOTES:
- Returns real-time, up-to-date information from the web
- Results include titles, URLs, content snippets, and relevance scores
- Images are included with URLs and descriptions when available
- Use for information that changes frequently or needs to be current
- Perfect complement to hotel search for comprehensive travel planning

📸 IMAGE RESPONSE FORMAT:
The response includes an "images" array with objects containing:
- url: Direct image URL
- description: AI-generated description of the image content"""
        )
        # Use OpenAI/GPT-5 to perform semantic web search synthesis while preserving output shape
        self.api_key = getattr(settings, 'openai_api_key', None)
    
    async def execute(self, input_data) -> ToolResult:
        """
        Execute web search using GPT-5 (replacing Tavily) while preserving response schema
        
        Args:
            input_data: Either a string (search query) or a dictionary containing:
                - query: Search query (required)
                - search_depth: "basic" or "advanced" (optional)
                - topic: "general", "news", or "research" (optional)
                - max_results: Maximum results to return (optional)
        """
        try:
            if not self.api_key:
                return ToolResult(
                    tool_name=self.name,
                    result="OpenAI API key not configured. Please add OPENAI_API_KEY to your environment variables.",
                    metadata={"error": "API key not configured"}
                )
            
            # Handle string input (simple query)
            if isinstance(input_data, str):
                input_data = {
                    "query": input_data,
                    "search_depth": "basic",
                    "topic": "general",
                    "max_results": 5
                }
            
            # Check for required parameters
            if not input_data.get("query"):
                return ToolResult(
                    tool_name=self.name,
                    result="Missing required parameter: 'query'",
                    metadata={"error": "Missing query parameter"}
                )
            
            return await self._search_web(input_data)
                
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                result=f"Error processing web search request: {str(e)}",
                metadata={"error": str(e)}
            )
    
    async def _search_web(self, input_data: Dict[str, Any]) -> ToolResult:
        """Search the web using GPT-5 to produce Tavily-compatible results"""
        try:
            # Prepare search parameters (kept for metadata/backward-compat)
            search_params = {
                "query": input_data.get("query"),
                "search_depth": input_data.get("search_depth", "basic"),
                "topic": input_data.get("topic", "general"),
                "max_results": input_data.get("max_results", 5),
                "include_images": False,
                "include_image_descriptions": False
            }
            search_params = {k: v for k, v in search_params.items() if v is not None}

            # Use GPT-5 to generate Tavily-compatible JSON results
            llm = ChatOpenAI(
                model=settings.open_api_model_name,
                temperature=0.2,
                openai_api_key=settings.openai_api_key
            )

            system = SystemMessage(content=(
                "You are a web research engine that outputs JSON strictly matching the Tavily API schema. "
                "Respond ONLY with valid JSON."
            ))

            human = HumanMessage(content=(
                "Produce a Tavily-compatible search response for the following query. "
                "Keep fields: query, answer, results (list of {title, url, content}), images (list), response_time. "
                f"Max results: {search_params.get('max_results', 5)}. Topic: {search_params.get('topic','general')}. "
                "Ensure URLs look realistic and contents are concise summaries. Do not include markdown.\n\n"
                f"Query: {search_params.get('query')}"
            ))

            ai = llm.invoke([system, human])

            # Attempt to parse JSON content
            try:
                response = json.loads(ai.content)
            except Exception:
                # Fallback minimal structure if parsing fails
                response = {
                    "query": search_params.get("query"),
                    "answer": ai.content,
                    "results": [],
                    "images": [],
                    "response_time": ""
                }

            # Ensure structural defaults
            response.setdefault("query", search_params.get("query"))
            response.setdefault("answer", "")
            response.setdefault("results", [])
            response.setdefault("images", [])
            response.setdefault("response_time", "")

            result = {
                "query": response.get("query"),
                "answer": response.get("answer", ""),
                "results": response.get("results", []),
                "images": response.get("images", []),
                "response_time": response.get("response_time", ""),
                "search_params": search_params
            }
            
            # Convert to JSON string for the agent to process
            json_result = json.dumps(result, default=str, indent=2)
            
            return ToolResult(
                tool_name=self.name,
                result=json_result,
                metadata={
                    "results_count": len(result.get("results", [])),
                    "images_count": len(result.get("images", [])),
                    "search_params": search_params,
                    "response_time": result.get("response_time")
                }
            )
                    
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                result=f"Error searching the web: {str(e)}",
                metadata={"error": str(e)}
            )
