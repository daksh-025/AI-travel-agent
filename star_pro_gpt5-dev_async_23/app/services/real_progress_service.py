import asyncio
import logging
from typing import AsyncGenerator, Optional, Callable
from app.chat.streaming_models import ProgressUpdate, ProgressPhase
from datetime import datetime

logger = logging.getLogger(__name__)


class RealProgressTracker:
    """Tracks real progress of AI agent processing"""
    
    def __init__(self):
        self.current_phase = ProgressPhase.STARTING
        self.current_message = "Initializing..."
        self.current_percentage = 0
        self.progress_callback: Optional[Callable] = None
        self.start_time = None
        
    def set_progress_callback(self, callback: Callable):
        """Set callback function to receive progress updates"""
        self.progress_callback = callback
        
    async def update_progress(self, phase: ProgressPhase, message: str, percentage: int = None):
        """Update current progress and notify callback"""
        self.current_phase = phase
        self.current_message = message
        if percentage is not None:
            self.current_percentage = percentage
            
        if self.progress_callback:
            try:
                await self.progress_callback(ProgressUpdate(
                    phase=phase,
                    message=message,
                    percentage=self.current_percentage,
                    details=f"Real-time progress: {datetime.now().strftime('%H:%M:%S')}"
                ))
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")
    
    async def start_processing(self):
        """Mark start of processing"""
        self.start_time = datetime.now()
        await self.update_progress(
            ProgressPhase.STARTING, 
            "Starting AI processing...", 
            0
        )
    
    async def analyzing_request(self):
        """Mark request analysis phase"""
        await self.update_progress(
            ProgressPhase.THINKING_PREFERENCES,
            "Analyzing your request and preferences...",
            15
        )
    
    async def tool_started(self, tool_name: str):
        """Mark when a tool starts executing"""
        if tool_name == "serpapi_hotels":
            await self.update_progress(
                ProgressPhase.SEARCHING_BOOKING,
                "Searching hotel databases (SerpAPI)...",
                30
            )
        elif tool_name == "serpapi_one_hotel":
            await self.update_progress(
                ProgressPhase.SEARCHING_BOOKING,
                "Getting detailed hotel information (SerpAPI)...",
                30
            )
        elif tool_name == "tavily_web_search":
            await self.update_progress(
                ProgressPhase.CHECKING_GOOGLE,
                "Searching web for current information...",
                35
            )
        elif tool_name == "pinecone_retrieve":
            await self.update_progress(
                ProgressPhase.ANALYZING_SITES,
                "Searching knowledge base for relevant info...",
                40
            )
        else:
            await self.update_progress(
                ProgressPhase.ANALYZING_SITES,
                f"Using {tool_name} tool...",
                45
            )
    
    async def tool_completed(self, tool_name: str, success: bool = True):
        """Mark when a tool completes"""
        if success:
            if tool_name == "serpapi_hotels":
                await self.update_progress(
                    ProgressPhase.ANALYZING_SITES,
                    "Processing hotel search results...",
                    65
                )
            elif tool_name == "serpapi_one_hotel":
                await self.update_progress(
                    ProgressPhase.ANALYZING_SITES,
                    "Processing hotel information...",
                    65
                )
            elif tool_name == "tavily_web_search":
                await self.update_progress(
                    ProgressPhase.ANALYZING_SITES,
                    "Processing web search results...",
                    60
                )
            else:
                await self.update_progress(
                    ProgressPhase.ANALYZING_SITES,
                    f"Completed {tool_name}, processing results...",
                    55
                )
        else:
            await self.update_progress(
                ProgressPhase.ANALYZING_SITES,
                f"Tool {tool_name} completed with issues, continuing...",
                50
            )
    
    async def matching_preferences(self):
        """Mark preference matching phase"""
        await self.update_progress(
            ProgressPhase.MATCHING_OPTIONS,
            "Matching results to your preferences...",
            75
        )
    
    async def generating_response(self):
        """Mark response generation phase"""
        await self.update_progress(
            ProgressPhase.GENERATING_RESPONSE,
            "Generating personalized response...",
            85
        )
    
    async def generating_suggestions(self):
        """Mark suggestion generation phase"""
        await self.update_progress(
            ProgressPhase.GENERATING_RESPONSE,
            "Creating follow-up suggestions...",
            95
        )
    
    async def completed(self):
        """Mark completion"""
        await self.update_progress(
            ProgressPhase.COMPLETE,
            "Complete!",
            100
        )


class RealProgressCallback:
    """Enhanced callback handler that tracks real AI agent progress"""
    
    def __init__(self, progress_tracker: RealProgressTracker):
        self.progress_tracker = progress_tracker
        self.tools_used = []
        self.tool_inputs = {}
        self.tool_outputs = {}
        self.current_tool = None
        
    def on_llm_start(self, serialized, prompts, **kwargs):
        """Called when LLM starts processing"""
        asyncio.create_task(self.progress_tracker.analyzing_request())
    
    def on_tool_start(self, serialized, input_str, **kwargs):
        """Called when a tool starts"""
        tool_name = serialized.get("name", "unknown")
        self.current_tool = tool_name
        self.tools_used.append(tool_name)
        self.tool_inputs[tool_name] = input_str
        
        # Update progress based on actual tool being used
        asyncio.create_task(self.progress_tracker.tool_started(tool_name))
    
    def on_tool_end(self, output, **kwargs):
        """Called when a tool ends"""
        if self.current_tool:
            self.tool_outputs[self.current_tool] = output
            # Check if tool was successful based on output
            success = output and not str(output).startswith("Error")
            asyncio.create_task(self.progress_tracker.tool_completed(self.current_tool, success))
            self.current_tool = None
    
    def on_tool_error(self, error, **kwargs):
        """Called when a tool errors"""
        if self.current_tool:
            asyncio.create_task(self.progress_tracker.tool_completed(self.current_tool, False))
            self.current_tool = None
    
    def on_agent_action(self, action, **kwargs):
        """Called when agent decides on an action"""
        # This is when the agent is thinking about what to do
        pass
    
    def on_agent_finish(self, finish, **kwargs):
        """Called when agent finishes"""
        asyncio.create_task(self.progress_tracker.matching_preferences())
    
    def on_llm_end(self, response, **kwargs):
        """Called when LLM completes"""
        if not self.tools_used:  # If no tools were used, this was just text generation
            asyncio.create_task(self.progress_tracker.generating_response())
    
    def get_tool_usage_info(self):
        """Get summary of tool usage (compatible with existing code)"""
        return {
            "tools_used": self.tools_used,
            "serpapi_hotels_used": "serpapi_hotels" in self.tools_used,
            "serpapi_one_hotel_used": "serpapi_one_hotel" in self.tools_used,
            "tavily_web_search_used": "tavily_web_search" in self.tools_used,
            "pinecone_retrieve_used": "pinecone_retrieve" in self.tools_used,
            "total_tools_used": len(self.tools_used),
            "tool_inputs": self.tool_inputs,
            "tool_outputs": self.tool_outputs,
        }


class RealProgressService:
    """Service that provides real progress tracking for AI agent processing"""
    
    @classmethod
    async def track_agent_progress(
        cls, 
        agent_task,
        progress_callback: Callable
    ) -> tuple:
        """
        Track real progress of agent processing
        
        Args:
            agent_task: The agent processing coroutine
            progress_callback: Callback function to receive progress updates
            
        Returns:
            Tuple of (agent_response, tool_usage_info)
        """
        # Create progress tracker
        progress_tracker = RealProgressTracker()
        progress_tracker.set_progress_callback(progress_callback)
        
        # Start progress tracking
        await progress_tracker.start_processing()
        
        try:
            # Execute the agent task with real progress tracking
            # Note: This would need to be integrated with the actual agent execution
            # For now, we'll simulate the phases based on typical processing
            
            # Start the agent task
            result = await agent_task
            
            # Mark completion
            await progress_tracker.completed()
            
            return result, {}
            
        except Exception as e:
            await progress_tracker.update_progress(
                ProgressPhase.COMPLETE,
                f"Error occurred: {str(e)[:50]}...",
                100
            )
            raise
    
    @classmethod
    async def create_progress_generator(
        cls,
        progress_updates: list
    ) -> AsyncGenerator[ProgressUpdate, None]:
        """
        Convert a list of progress updates into an async generator
        
        Args:
            progress_updates: List of ProgressUpdate objects
            
        Yields:
            ProgressUpdate objects
        """
        for update in progress_updates:
            yield update
            await asyncio.sleep(0.1)  # Small delay for realistic feel
