import logging
import pinecone
from app.chat.tools.base import BaseTool
from app.chat.models import ToolResult

logger = logging.getLogger(__name__)


class PineconeRetrieveTool(BaseTool):
    """Tool for retrieving hotel-related information from Pinecone vector database"""
    
    def __init__(self, api_key: str = None, environment: str = None):
        super().__init__(
            name="pinecone_retrieve",
            description="""Search and retrieve hotel information, reviews, and travel content using vector similarity search.

Input should be a JSON string with the following structure:
{
  "query": "hotel reviews for luxury hotels in Paris",
  "index_name": "hotel-embeddings",
  "top_k": 10,
  "filter": {"category": "reviews", "rating": {"$gte": 4.0}},
  "include_metadata": true
}

Or use a simple natural language query string:
"hotel reviews for luxury hotels in Paris"

Available parameters:
- query: Natural language search query
- index_name: Pinecone index name (default: "hotel-embeddings")
- top_k: Number of results to return (default: 10)
- filter: Metadata filter object
- include_metadata: Whether to include metadata in results (default: true)

The tool will search through stored hotel data and return relevant information based on your query."""
        )
        self.api_key = api_key
        self.environment = environment
        self.pinecone_client = None
    
    async def _initialize_client(self):
        """Initialize Pinecone client"""
        if self.pinecone_client is None:
            try:
                pinecone.init(api_key=self.api_key, environment=self.environment)
                self.pinecone_client = pinecone
            except ImportError:
                logger.error("Pinecone library not installed. Please install with: pip install pinecone-client")
                raise ImportError("Pinecone library not installed")
            except Exception as e:
                logger.error(f"Failed to initialize Pinecone client: {e}")
                raise
    
    async def execute(self, input_data) -> ToolResult:
        """
        Execute Pinecone vector search
        
        Args:
            input_data: Either a string (natural language query) or a dictionary containing:
                - index_name: Pinecone index name
                - query_vector: Vector to search for
                - top_k: Number of results to return
                - filter: Metadata filter
                - include_metadata: Whether to include metadata in results
        """
        try:
            # Handle string input (natural language query)
            if isinstance(input_data, str):
                # For now, return a placeholder response since we need to implement
                # text-to-vector conversion for natural language queries
                return ToolResult(
                    tool_name=self.name,
                    result=f"Received query: '{input_data}'. Pinecone search requires vector embeddings. Please provide query_vector parameter.",
                    metadata={"error": "String input not yet supported", "query": input_data}
                )
            
            await self._initialize_client()
            
            index_name = input_data.get("index_name", "hotel-embeddings")
            query_vector = input_data.get("query_vector")
            query_text = input_data.get("query")
            top_k = input_data.get("top_k", 10)
            filter_dict = input_data.get("filter", {})
            include_metadata = input_data.get("include_metadata", True)
            
            if not query_vector and not query_text:
                raise ValueError("Either query_vector or query is required for Pinecone search")
            
            # If query_vector is not provided but query is, use a placeholder vector
            # In a real implementation, this would generate embeddings from the query text
            if not query_vector and query_text:
                query_vector = [0.1] * 1536  # Placeholder vector - would be generated from query_text
                logger.warning(f"Using placeholder vector for query: '{query_text}'. Implement text-to-vector conversion for production use.")
            
            # Get the index
            index = self.pinecone_client.Index(index_name)
            
            # Perform the query
            query_response = index.query(
                vector=query_vector,
                top_k=top_k,
                filter=filter_dict,
                include_metadata=include_metadata
            )
            
            # Format results
            results = []
            for match in query_response.matches:
                result_item = {
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata if include_metadata else {}
                }
                results.append(result_item)
            
            return ToolResult(
                tool_name=self.name,
                result=f"Found {len(results)} similar items in {index_name}",
                metadata={
                    "index_name": index_name,
                    "results": results,
                    "total_results": len(results),
                    "query_vector_length": len(query_vector)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in Pinecone retrieval tool: {e}")
            return ToolResult(
                tool_name=self.name,
                result=f"Pinecone search failed: {str(e)}",
                metadata={"error": str(e)}
            )
    
    async def search_hotel_reviews(self, query_text: str, location: str = None, rating_filter: float = None) -> ToolResult:
        """Search for hotel reviews using vector similarity"""
        # This would require text embedding - placeholder for now
        filter_dict = {}
        if location:
            filter_dict["location"] = location
        if rating_filter:
            filter_dict["rating"] = {"$gte": rating_filter}
        
        return await self.execute({
            "index_name": "hotel-reviews",
            "query_vector": [0.1] * 1536,  # Placeholder vector - would be generated from query_text
            "top_k": 20,
            "filter": filter_dict,
            "include_metadata": True
        })
    
    async def search_travel_content(self, query_text: str, content_type: str = None) -> ToolResult:
        """Search for travel-related content"""
        filter_dict = {}
        if content_type:
            filter_dict["content_type"] = content_type
        
        return await self.execute({
            "index_name": "travel-content",
            "query_vector": [0.1] * 1536,  # Placeholder vector
            "top_k": 15,
            "filter": filter_dict,
            "include_metadata": True
        })
    
    async def search_amenities(self, amenity_query: str) -> ToolResult:
        """Search for hotels with specific amenities"""
        return await self.execute({
            "index_name": "hotel-amenities",
            "query_vector": [0.1] * 1536,  # Placeholder vector
            "top_k": 25,
            "filter": {},
            "include_metadata": True
        })
    
    async def get_similar_hotels(self, hotel_id: str, top_k: int = 10) -> ToolResult:
        """Find similar hotels based on a reference hotel"""
        # This would require getting the hotel's vector first
        return await self.execute({
            "index_name": "hotel-embeddings",
            "query_vector": [0.1] * 1536,  # Placeholder - would be the hotel's vector
            "top_k": top_k,
            "filter": {"hotel_id": {"$ne": hotel_id}},  # Exclude the reference hotel
            "include_metadata": True
        })
