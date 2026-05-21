import asyncio
import logging
from typing import AsyncGenerator, Optional
from app.chat.models import ChatRequest
from app.chat.streaming_models import (
    StreamingEvent, ProgressEvent, ProgressUpdate, ProgressPhase
)
from app.chat.agent import HotelChatAgent, RealProgressCallback
import uuid

logger = logging.getLogger(__name__)


class StreamingAgentService:
    """Service that provides real-time streaming of agent processing with progress"""
    
    def __init__(self, agent: HotelChatAgent):
        self.agent = agent
        self.progress_queue = None
        
    async def process_with_streaming_progress(
        self, 
        request: ChatRequest,
        session_id: str,
        tab_id: Optional[str] = None
    ) -> AsyncGenerator[StreamingEvent, None]:
        """
        Process a chat request with real-time progress streaming
        
        Args:
            request: Chat request
            session_id: Session ID
            tab_id: Optional tab ID
            
        Yields:
            StreamingEvent objects including progress updates
        """
        # Create a queue for progress updates
        self.progress_queue = asyncio.Queue()
        
        # Create progress callback that puts updates in the queue
        async def progress_callback(progress_update: ProgressUpdate):
            await self.progress_queue.put(progress_update)
        
        # Start the agent processing in a background task
        agent_task = asyncio.create_task(
            self.agent.process_message_with_progress(request, progress_callback)
        )
        
        # Stream progress updates as they come in
        try:
            while True:
                # Check if agent is done
                if agent_task.done():
                    # Process any remaining progress updates
                    while not self.progress_queue.empty():
                        try:
                            progress_update = self.progress_queue.get_nowait()
                            yield ProgressEvent(
                                session_id=session_id,
                                tab_id=tab_id,
                                progress=progress_update
                            )
                        except asyncio.QueueEmpty:
                            break
                    
                    # Get the agent result
                    response = await agent_task
                    
                    # The response will be handled by the caller
                    break
                
                # Wait for progress updates with timeout
                try:
                    progress_update = await asyncio.wait_for(
                        self.progress_queue.get(), 
                        timeout=0.1
                    )
                    
                    yield ProgressEvent(
                        session_id=session_id,
                        tab_id=tab_id,
                        progress=progress_update
                    )
                    
                except asyncio.TimeoutError:
                    # No progress update received, continue checking
                    continue
                    
        except Exception as e:
            logger.error(f"Error in streaming agent service: {e}")
            # Cancel the agent task if still running
            if not agent_task.done():
                agent_task.cancel()
            raise


class SimpleProgressTracker:
    """Simple progress tracker that provides basic real progress updates"""
    
    @staticmethod
    async def track_basic_progress(
        session_id: str,
        tab_id: Optional[str],
        request: ChatRequest
    ) -> AsyncGenerator[ProgressEvent, None]:
        """
        Provide basic progress tracking based on request analysis
        
        Args:
            session_id: Session ID
            tab_id: Tab ID
            request: Chat request
            
        Yields:
            ProgressEvent objects with basic progress
        """
        # Analyze request to determine likely processing steps
        message_lower = request.message.lower()
        
        is_hotel_search = any(keyword in message_lower for keyword in [
            "hotel", "accommodation", "stay", "booking", "room", "resort"
        ])
        is_web_search = any(keyword in message_lower for keyword in [
            "weather", "restaurant", "attraction", "current", "news", "what's"
        ])
        
        # Step 1: Starting
        yield ProgressEvent(
            session_id=session_id,
            tab_id=tab_id,
            progress=ProgressUpdate(
                phase=ProgressPhase.STARTING,
                message="Starting AI processing...",
                percentage=5,
                details="Analyzing your request"
            )
        )
        await asyncio.sleep(0.3)
        
        # Step 2: Analyzing
        yield ProgressEvent(
            session_id=session_id,
            tab_id=tab_id,
            progress=ProgressUpdate(
                phase=ProgressPhase.THINKING_PREFERENCES,
                message="AI is analyzing your request...",
                percentage=15,
                details="Understanding your needs"
            )
        )
        await asyncio.sleep(0.5)
        
        # Step 3: Tool usage (if applicable)
        if is_hotel_search:
            yield ProgressEvent(
                session_id=session_id,
                tab_id=tab_id,
                progress=ProgressUpdate(
                    phase=ProgressPhase.SEARCHING_BOOKING,
                    message="Searching hotel databases...",
                    percentage=35,
                    details="Checking Booking.com, Google Hotels"
                )
            )
            await asyncio.sleep(1.0)
            
            yield ProgressEvent(
                session_id=session_id,
                tab_id=tab_id,
                progress=ProgressUpdate(
                    phase=ProgressPhase.ANALYZING_SITES,
                    message="Processing hotel search results...",
                    percentage=65,
                    details="Analyzing found hotels"
                )
            )
            await asyncio.sleep(0.7)
            
        elif is_web_search:
            yield ProgressEvent(
                session_id=session_id,
                tab_id=tab_id,
                progress=ProgressUpdate(
                    phase=ProgressPhase.CHECKING_GOOGLE,
                    message="Searching web for current information...",
                    percentage=40,
                    details="Gathering real-time data"
                )
            )
            await asyncio.sleep(0.8)
            
            yield ProgressEvent(
                session_id=session_id,
                tab_id=tab_id,
                progress=ProgressUpdate(
                    phase=ProgressPhase.ANALYZING_SITES,
                    message="Processing web search results...",
                    percentage=60,
                    details="Analyzing found information"
                )
            )
            await asyncio.sleep(0.5)
        
        # Step 4: Matching preferences
        yield ProgressEvent(
            session_id=session_id,
            tab_id=tab_id,
            progress=ProgressUpdate(
                phase=ProgressPhase.MATCHING_OPTIONS,
                message="Matching results to your preferences...",
                percentage=75,
                details="Personalizing recommendations"
            )
        )
        await asyncio.sleep(0.4)
        
        # Step 5: Generating response
        yield ProgressEvent(
            session_id=session_id,
            tab_id=tab_id,
            progress=ProgressUpdate(
                phase=ProgressPhase.GENERATING_RESPONSE,
                message="Creating personalized response...",
                percentage=85,
                details="Preparing your answer"
            )
        )
        await asyncio.sleep(0.6)
        
        # Step 6: Complete
        yield ProgressEvent(
            session_id=session_id,
            tab_id=tab_id,
            progress=ProgressUpdate(
                phase=ProgressPhase.COMPLETE,
                message="Complete!",
                percentage=100,
                details="Processing finished"
            )
        )
