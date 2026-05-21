import logging
from typing import List, Dict, Any, Optional, AsyncGenerator, Literal
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.chat.models import ChatRequest, ChatSession, ChatTab, UpdateTabRequest, TabResponse
from app.chat.response_models import StructuredChatResponse
from app.chat.streaming_models import (
    StreamingEvent, ProgressEvent, TextChunkEvent, HotelResultsEvent, 
    WebResultsEvent, SuggestionsEvent, CompleteEvent, ErrorEvent,
    ProgressUpdate, ProgressPhase
)
from app.chat.agent import HotelChatAgent
from app.repositories.chat_repository import ChatRepository
from app.services.hybrid_memory_service import HybridMemoryService
from app.services.progress_service import ProgressService
from app.services.text_streaming_service import TextStreamingService
from app.services.streaming_agent_service import SimpleProgressTracker
from app.core.config import settings
import uuid
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class ChatService:
    """Service layer for chat functionality"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.chat_repository = ChatRepository(db)
        self.hybrid_memory = HybridMemoryService(self.chat_repository)
        self.agent = HotelChatAgent(db, self.hybrid_memory)
    
    async def generate_tab_name_suggestion(self, user_message: str) -> str:
        """
        Generate a suggested tab name based on the user's first message
        
        Args:
            user_message: The user's first message in the conversation
            
        Returns:
            Suggested tab name
        """
        try:
            # Create a simple prompt for tab name generation
            prompt = f"""
            Based on this user message, suggest a short, descriptive tab name (max 30 characters):
            
            User message: "{user_message}"
            
            Rules:
            - Keep it under 30 characters
            - Make it descriptive but concise
            - Focus on the main topic or intent
            - Use title case
            - Avoid generic terms like "Chat" or "Conversation"
            
            Suggested tab name:"""
            
            # Use the agent's LLM to generate the suggestion
            await self.agent._initialize_llm()
            if self.agent.llm:
                from langchain.schema import HumanMessage
                response = await self.agent.llm.ainvoke([HumanMessage(content=prompt)])
                suggested_name = response.content.strip().strip('"').strip("'")
                
                # Clean up the response and ensure it's within limits
                if len(suggested_name) > 30:
                    suggested_name = suggested_name[:27] + "..."
                
                # Fallback if the response is empty or too generic
                if not suggested_name or suggested_name.lower() in ["new chat", "chat", "conversation"]:
                    # Extract key words from the message
                    words = user_message.split()[:3]
                    suggested_name = " ".join(words).title()
                    if len(suggested_name) > 30:
                        suggested_name = suggested_name[:27] + "..."
                
                return suggested_name
            else:
                # Fallback if LLM is not available
                words = user_message.split()[:3]
                return " ".join(words).title()[:30]
                
        except Exception as e:
            logger.error(f"Error generating tab name suggestion: {e}")
            # Fallback to first few words of the message
            words = user_message.split()[:3]
            return " ".join(words).title()[:30]

    async def process_chat_message(self, request: ChatRequest, user_id: Optional[str] = None) -> StructuredChatResponse:
        """
        Process a chat message and return a structured response
        
        Args:
            request: Chat request containing message and session info
            user_id: Optional user ID for authenticated users
            
        Returns:
            StructuredChatResponse with AI response and session info
        """
        try:
            is_new_tab = False
            
            # Handle tab-based session management
            if request.tab_id and user_id:
                # Get or create tab and session
                tab = await self.chat_repository.get_tab(request.tab_id)
                if not tab:
                    raise ValueError(f"Tab {request.tab_id} not found")
                
                # Use tab's session_id
                request.session_id = tab.session_id
                
                # Check if this is the first message in the tab
                if tab.message_count == 0:
                    is_new_tab = True
                
                # Update tab activity
                await self.chat_repository.update_tab_activity(request.tab_id)
            elif user_id and not request.session_id:
                # Create new tab and session for authenticated user
                tab = await self.create_new_tab(user_id, "New Chat")
                request.session_id = tab.session_id
                request.tab_id = tab.tab_id
                is_new_tab = True
            
            # Set user context for traveller type retrieval
            if user_id and not request.context:
                request.context = {"user_id": user_id}
            elif user_id and request.context:
                request.context["user_id"] = user_id
            
            # Process with LangChain agent (now with proper chat history management)
            response = await self.agent.process_message(request)
            
            # Store messages in hybrid memory (both Redis and MongoDB)
            await self.hybrid_memory.add_user_message(response.session_id, request.message, user_id)
            
            # Store the assistant's final summary text and structured results
            message_content = response.message or "No message content"
            
            # Prepare metadata with structured results
            metadata = {}
            if response.hotelSearch:
                metadata["hotelSearch"] = {
                    "resultsTitle": response.hotelSearch.resultsTitle,
                    "results": [
                        {
                            "id": hotel.id,
                            "name": hotel.name,
                            "link": hotel.link,
                            "description": hotel.description,
                            "rating": hotel.rating,
                            "reviews": hotel.reviews,
                            "stars": hotel.stars,
                            "address": hotel.address,
                            "phone": hotel.phone,
                            "features": hotel.features,
                            "price": hotel.price,
                            "priceLabel": hotel.priceLabel,
                            "roomType": hotel.roomType,
                            "source": hotel.source,
                            "sourceUrl": hotel.sourceUrl,
                            "imageUrls": hotel.imageUrls,
                            "aiNote": hotel.aiNote,
                            "position": {
                                "lat": hotel.position.lat,
                                "lng": hotel.position.lng
                            } if hotel.position else None,
                            "extra_prices": [
                                {
                                    "source": extra_price.source,
                                    "source_url": extra_price.source_url,
                                    "price": extra_price.price
                                }
                                for extra_price in hotel.extra_prices
                            ] if hotel.extra_prices else []
                        }
                        for hotel in response.hotelSearch.results
                    ]
                }
            
            if response.webSearch:
                metadata["webSearch"] = {
                    "resultsTitle": response.webSearch.resultsTitle,
                    "images": [
                        {
                            "url": img.url,
                            "description": img.description
                        }
                        for img in response.webSearch.images
                    ]
                }
            
            # Store message with metadata
            await self.hybrid_memory.add_ai_message_with_metadata(response.session_id, message_content, metadata, user_id)
            
            # Update tab with new message count
            if request.tab_id:
                await self.chat_repository.increment_tab_message_count(request.tab_id)
                
                # Generate and update tab name if this is the first message
                if is_new_tab and user_id:
                    try:
                        suggested_name = await self.generate_tab_name_suggestion(request.message)
                        await self.chat_repository.update_tab_title(request.tab_id, suggested_name)
                        # Update the response to include the new tab name
                        response.tab_name_suggestion = suggested_name
                        logger.info(f"Updated tab {request.tab_id} with suggested name: {suggested_name}")
                    except Exception as e:
                        logger.error(f"Error updating tab name: {e}")
                        # Continue without failing the main request
            
            # Add tab_id to response
            response.tab_id = request.tab_id
            
            return response
            
        except Exception as e:
            logger.error(f"Error in chat service: {e}")
            # Generate fallback suggestions even on error
            try:
                suggestions = await self.agent.generate_suggestions(request.message, [])
            except:
                suggestions = [
                    "Find me nearby attractions",
                    "Show me luxury resorts", 
                    "What's the best time to visit?"
                ]
            
            return StructuredChatResponse(
                message="I apologize, but I'm having trouble processing your request right now. Please try again later.",
                session_id=request.session_id or "error-session",
                tab_id=request.tab_id,
                suggestions=suggestions,
                metadata={"error": str(e)}
            )

    async def process_chat_message_stream(
        self, 
        request: ChatRequest, 
        user_id: Optional[str] = None,
        enable_progress: bool = True,
        streaming_speed: Literal["fast", "normal", "slow"] = "normal"
    ) -> AsyncGenerator[StreamingEvent, None]:
        """
        Process a chat message and return streaming events
        
        Args:
            request: Chat request containing message and session info
            user_id: Optional user ID for authenticated users
            enable_progress: Whether to send progress updates
            streaming_speed: Speed of text streaming
            
        Yields:
            StreamingEvent objects for progress, text chunks, results, etc.
        """
        session_id = request.session_id or str(uuid.uuid4())
        
        try:
            # Handle tab-based session management (same as regular method)
            is_new_tab = False
            if request.tab_id and user_id:
                tab = await self.chat_repository.get_tab(request.tab_id)
                if not tab:
                    yield ErrorEvent(
                        session_id=session_id,
                        tab_id=request.tab_id,
                        error_message=f"Tab {request.tab_id} not found"
                    )
                    return
                
                request.session_id = tab.session_id
                session_id = tab.session_id
                
                if tab.message_count == 0:
                    is_new_tab = True
                
                await self.chat_repository.update_tab_activity(request.tab_id)
            elif user_id and not request.session_id:
                tab = await self.create_new_tab(user_id, "New Chat")
                request.session_id = tab.session_id
                request.tab_id = tab.tab_id
                session_id = tab.session_id
                is_new_tab = True
            
            # Set user context
            if user_id and not request.context:
                request.context = {"user_id": user_id}
            elif user_id and request.context:
                request.context["user_id"] = user_id
            
            # Add user message to memory
            await self.hybrid_memory.add_user_message(session_id, request.message, user_id)
            
            # Process the message with REAL progress tracking
            if enable_progress:
                # Start the agent processing in the background
                agent_task = asyncio.create_task(self.agent.process_message(request))
                
                # Stream realistic progress updates while processing
                progress_tracker = SimpleProgressTracker.track_basic_progress(
                    session_id, request.tab_id, request
                )
                
                # Stream progress updates until agent completes
                async for progress_event in progress_tracker:
                    yield progress_event
                    
                    # Check if agent is done
                    if agent_task.done():
                        break
                
                # Get the response
                response = await agent_task
                
                # Send final completion if not already sent
                if not agent_task.done():
                    yield ProgressEvent(
                        session_id=session_id,
                        tab_id=request.tab_id,
                        progress=ProgressUpdate(
                            phase=ProgressPhase.COMPLETE,
                            message="Complete!",
                            percentage=100,
                            details="Processing finished"
                        )
                    )
            else:
                # Process without progress tracking
                response = await self.agent.process_message(request)
            
            # Log response details for debugging
            logger.info(f"=" * 80)
            logger.info(f"🔍 STREAMING SERVICE - Received response from agent")
            logger.info(f"Response hotelSearch is None: {response.hotelSearch is None}")
            logger.info(f"Response webSearch is None: {response.webSearch is None}")
            logger.info(f"Response message length: {len(response.message) if response.message else 0}")
            
            if response.hotelSearch:
                logger.info(f"🏨 Hotel search data exists: {response.hotelSearch.resultsTitle}")
                logger.info(f"🏨 Hotel results count: {len(response.hotelSearch.results)}")
            
            if response.webSearch:
                logger.info(f"🌐 Web search data exists: {response.webSearch.resultsTitle}")
                logger.info(f"🌐 Web images count: {len(response.webSearch.images)}")
            
            logger.info(f"=" * 80)
            
            # Stream the text response FIRST for immediate user feedback
            if response.message:
                logger.info(f"💬 Starting text streaming first for better UX")
                async for text_event in TextStreamingService.stream_text(
                    response.message,
                    session_id,
                    request.tab_id,
                    streaming_speed
                ):
                    yield text_event
            
            # Small delay after text streaming to let it render before structured results
            await asyncio.sleep(0.3)
            
            # Stream hotel results after text streaming
            if response.hotelSearch:
                logger.info(f"🏨 Sending hotel results: {response.hotelSearch.resultsTitle}")
                logger.info(f"🏨 Hotel results count: {len(response.hotelSearch.results)}")
                
                hotel_data = {
                    "resultsTitle": response.hotelSearch.resultsTitle,
                    "results": [
                        {
                            "id": hotel.id,
                            "name": hotel.name,
                            "link": hotel.link,
                            "description": hotel.description,
                            "rating": hotel.rating,
                            "reviews": hotel.reviews,
                            "stars": hotel.stars,
                            "address": hotel.address,
                            "phone": hotel.phone,
                            "features": hotel.features,
                            "price": hotel.price,
                            "priceLabel": hotel.priceLabel,
                            "roomType": hotel.roomType,
                            "source": hotel.source,
                            "sourceUrl": hotel.sourceUrl,
                            "imageUrls": hotel.imageUrls,
                            "aiNote": hotel.aiNote,
                            "position": {
                                "lat": hotel.position.lat,
                                "lng": hotel.position.lng
                            } if hotel.position else None,
                            "extra_prices": [
                                {
                                    "source": extra_price.source,
                                    "source_url": extra_price.source_url,
                                    "price": extra_price.price
                                }
                                for extra_price in hotel.extra_prices
                            ] if hotel.extra_prices else None
                        }
                        for hotel in response.hotelSearch.results
                    ]
                }
                
                hotel_event = HotelResultsEvent(
                    session_id=session_id,
                    tab_id=request.tab_id,
                    hotel_search=hotel_data
                )
                logger.info(f"🏨 Generated hotel event - session: {session_id}, tab: {request.tab_id}")
                logger.info(f"🏨 Hotel event type: {hotel_event.event_type}")
                logger.info(f"🏨 Hotel data keys: {list(hotel_data.keys())}")
                logger.info(f"🏨 Hotel results in event: {len(hotel_data['results'])}")
                logger.info(f"🚀 YIELDING HOTEL EVENT NOW!")
                yield hotel_event
                logger.info(f"✅ Hotel event yielded successfully")
            
            # Stream web search results if available (independent of hotel results)
            if response.webSearch:
                logger.info(f"🌐 Processing web search results...")
                web_data = {
                    "resultsTitle": response.webSearch.resultsTitle,
                    "images": [
                        {
                            "url": img.url,
                            "description": img.description
                        }
                        for img in response.webSearch.images
                    ]
                }
                
                logger.info(f"🌐 Web data prepared - {len(web_data['images'])} images")
                logger.info(f"🚀 YIELDING WEB RESULTS EVENT NOW!")
                yield WebResultsEvent(
                    session_id=session_id,
                    tab_id=request.tab_id,
                    web_search=web_data
                )
                logger.info(f"✅ Web event yielded successfully")
            
            
            # Send suggestions
            if response.suggestions:
                yield SuggestionsEvent(
                    session_id=session_id,
                    tab_id=request.tab_id,
                    suggestions=response.suggestions
                )
            
            # Store the assistant's final summary text and structured results
            message_content = response.message or "No message content"
            
            # Prepare metadata with structured results
            metadata = {}
            if response.hotelSearch:
                metadata["hotelSearch"] = {
                    "resultsTitle": response.hotelSearch.resultsTitle,
                    "results": [
                        {
                            "id": hotel.id,
                            "name": hotel.name,
                            "link": hotel.link,
                            "description": hotel.description,
                            "rating": hotel.rating,
                            "reviews": hotel.reviews,
                            "stars": hotel.stars,
                            "address": hotel.address,
                            "phone": hotel.phone,
                            "features": hotel.features,
                            "price": hotel.price,
                            "priceLabel": hotel.priceLabel,
                            "roomType": hotel.roomType,
                            "source": hotel.source,
                            "sourceUrl": hotel.sourceUrl,
                            "imageUrls": hotel.imageUrls,
                            "aiNote": hotel.aiNote,
                            "position": {
                                "lat": hotel.position.lat,
                                "lng": hotel.position.lng
                            } if hotel.position else None,
                            "extra_prices": [
                                {
                                    "source": extra_price.source,
                                    "source_url": extra_price.source_url,
                                    "price": extra_price.price
                                }
                                for extra_price in hotel.extra_prices
                            ] if hotel.extra_prices else []
                        }
                        for hotel in response.hotelSearch.results
                    ]
                }
            
            if response.webSearch:
                metadata["webSearch"] = {
                    "resultsTitle": response.webSearch.resultsTitle,
                    "images": [
                        {
                            "url": img.url,
                            "description": img.description
                        }
                        for img in response.webSearch.images
                    ]
                }
            
            # Store message with metadata
            await self.hybrid_memory.add_ai_message_with_metadata(session_id, message_content, metadata, user_id)
            
            # Update tab with new message count
            if request.tab_id:
                await self.chat_repository.increment_tab_message_count(request.tab_id)
                
                # Generate and update tab name if this is the first message
                if is_new_tab and user_id:
                    try:
                        suggested_name = await self.generate_tab_name_suggestion(request.message)
                        await self.chat_repository.update_tab_title(request.tab_id, suggested_name)
                        # Update the response to include the new tab name
                        response.tab_name_suggestion = suggested_name
                        logger.info(f"Updated tab {request.tab_id} with suggested name: {suggested_name}")
                    except Exception as e:
                        logger.warning(f"Could not update tab name: {e}")
            
            # Send completion event
            completion_metadata = {
                "model": response.metadata.get("model") if response.metadata else settings.open_api_model_name,
                "history_length": response.metadata.get("history_length") if response.metadata else 0,
                "tab_name_suggestion": response.tab_name_suggestion
            }
            logger.info(f"Sending completion event with tab_name_suggestion: {response.tab_name_suggestion}")
            
            yield CompleteEvent(
                session_id=session_id,
                tab_id=request.tab_id,
                final_message=response.message or "",
                metadata=completion_metadata
            )
            
        except Exception as e:
            logger.error(f"Error in streaming chat service: {e}")
            yield ErrorEvent(
                session_id=session_id,
                tab_id=request.tab_id,
                error_message=f"Error processing chat message: {str(e)}"
            )

    async def create_new_tab(self, user_id: str, title: str = "New Chat") -> ChatTab:
        """
        Create a new chat tab for a user
        
        Args:
            user_id: User identifier
            title: Tab title
            
        Returns:
            Newly created ChatTab
        """
        try:
            # Generate unique IDs
            tab_id = str(uuid.uuid4())
            session_id = str(uuid.uuid4())
            
            # Create new session
            session = ChatSession(
                session_id=session_id,
                user_id=user_id,
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                message_count=0,
                is_active=True
            )
            await self.chat_repository.create_session(session)
            
            # Create new tab
            tab = ChatTab(
                tab_id=tab_id,
                user_id=user_id,
                title=title,
                session_id=session_id,
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                message_count=0,
                is_active=True,
                is_pinned=False,
                order_index=0
            )
            created_tab = await self.chat_repository.create_tab(tab)
            
            logger.info(f"Created new tab {tab_id} for user {user_id}")
            return created_tab
            
        except Exception as e:
            logger.error(f"Error creating new tab for user {user_id}: {e}")
            raise

    async def get_user_tabs(self, user_id: str) -> List[TabResponse]:
        """
        Get all tabs for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            List of user's tabs
        """
        try:
            tabs = await self.chat_repository.get_user_tabs(user_id)
            return [
                TabResponse(
                    tab_id=tab.tab_id,
                    title=tab.title,
                    session_id=tab.session_id,
                    created_at=tab.created_at,
                    last_activity=tab.last_activity,
                    message_count=tab.message_count,
                    is_active=tab.is_active,
                    is_pinned=tab.is_pinned,
                    order_index=tab.order_index
                )
                for tab in tabs
            ]
        except Exception as e:
            logger.error(f"Error getting tabs for user {user_id}: {e}")
            return []

    async def update_tab(self, tab_id: str, user_id: str, update_data: UpdateTabRequest) -> bool:
        """
        Update a tab
        
        Args:
            tab_id: Tab identifier
            user_id: User identifier for validation
            update_data: Update data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate tab ownership
            tab = await self.chat_repository.get_tab(tab_id)
            if not tab or tab.user_id != user_id:
                logger.warning(f"User {user_id} attempted to update tab {tab_id} owned by {tab.user_id if tab else 'unknown'}")
                return False
            
            # Prepare update data
            update_dict = {}
            if update_data.title is not None:
                update_dict["title"] = update_data.title
            if update_data.is_pinned is not None:
                update_dict["is_pinned"] = update_data.is_pinned
            if update_data.order_index is not None:
                update_dict["order_index"] = update_data.order_index
            
            return await self.chat_repository.update_tab(tab_id, update_dict)
            
        except Exception as e:
            logger.error(f"Error updating tab {tab_id}: {e}")
            return False

    async def delete_tab(self, tab_id: str, user_id: str) -> bool:
        """
        Delete a tab and its associated session
        
        Args:
            tab_id: Tab identifier
            user_id: User identifier for validation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate tab ownership
            tab = await self.chat_repository.get_tab(tab_id)
            if not tab or tab.user_id != user_id:
                logger.warning(f"User {user_id} attempted to delete tab {tab_id} owned by {tab.user_id if tab else 'unknown'}")
                return False
            
            return await self.chat_repository.delete_tab(tab_id)
            
        except Exception as e:
            logger.error(f"Error deleting tab {tab_id}: {e}")
            return False

    async def _update_tab_message_count(self, tab_id: str):
        """Update tab message count"""
        try:
            tab = await self.chat_repository.get_tab(tab_id)
            if tab:
                # Get current message count for the session
                messages = await self.chat_repository.get_messages_by_session(tab.session_id)
                await self.chat_repository.update_tab_activity(tab_id, len(messages))
        except Exception as e:
            logger.error(f"Error updating tab message count for {tab_id}: {e}")
    
    async def get_conversation_history(self, session_id: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session
        
        Args:
            session_id: Session identifier
            user_id: Optional user ID for validation
            
        Returns:
            List of conversation messages
        """
        try:
            # Validate session ownership if user_id provided
            if user_id:
                session = await self.chat_repository.get_session(session_id)
                if session and session.user_id != user_id:
                    logger.warning(f"User {user_id} attempted to access session {session_id} owned by {session.user_id}")
                    return []
            
            # Get history from MongoDB (more reliable for API responses)
            return await self.hybrid_memory.get_mongodb_history(session_id)
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    async def clear_conversation(self, session_id: str, user_id: Optional[str] = None) -> bool:
        """
        Clear conversation history for a session
        
        Args:
            session_id: Session identifier
            user_id: Optional user ID for validation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate session ownership if user_id provided
            if user_id:
                session = await self.chat_repository.get_session(session_id)
                if session and session.user_id != user_id:
                    logger.warning(f"User {user_id} attempted to clear session {session_id} owned by {session.user_id}")
                    return False
            
            # Clear from both Redis and MongoDB
            return await self.hybrid_memory.clear_conversation_history(session_id)
            
        except Exception as e:
            logger.error(f"Error clearing conversation: {e}")
            return False
    
    async def get_user_sessions(self, user_id: str) -> List[ChatSession]:
        """
        Get all chat sessions for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            List of chat sessions
        """
        try:
            return await self.hybrid_memory.get_user_sessions(user_id)
            
        except Exception as e:
            logger.error(f"Error getting user sessions: {e}")
            return []
    
    async def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get statistics for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with session statistics
        """
        try:
            return await self.hybrid_memory.get_session_stats(session_id)
            
        except Exception as e:
            logger.error(f"Error getting session stats: {e}")
            return {}
    
    async def clear_all_user_history(self, user_id: str) -> bool:
        """
        Clear all chat history for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Clear all Redis memory for the user
            await self.hybrid_memory.clear_all_user_memory(user_id)
            
            # Delete all user data from MongoDB efficiently
            deleted_counts = await self.chat_repository.delete_all_user_data(user_id)
            
            logger.info(f"Cleared all chat history for user {user_id}: {deleted_counts}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing all user history for {user_id}: {e}")
            return False

    async def process_chat_message_realtime_streaming(
        self, 
        request: ChatRequest, 
        user_id: Optional[str] = None,
        streaming_speed: Literal["fast", "normal", "slow"] = "normal"
    ) -> AsyncGenerator[StreamingEvent, None]:
        """
        Process chat message with real-time streaming during agent execution
        
        This method streams text as soon as possible after tavily_web_search
        and continues calling serpapi_one_hotel while streaming.
        """
        try:
            # Generate session ID if not provided
            session_id = request.session_id or str(uuid.uuid4())
            
            # Store user message in memory
            await self.hybrid_memory.add_user_message(session_id, request.message, user_id)
            
            # Create a queue to collect intermediate streaming text
            intermediate_text_queue = []
            
            async def streaming_callback(text: str):
                """Callback to handle intermediate streaming text"""
                logger.info(f"🔄 Realtime streaming callback received: {text[:100]}...")
                intermediate_text_queue.append(text)
                
                # Stream the intermediate text immediately
                async for text_event in TextStreamingService.stream_text(
                    text,
                    session_id,
                    request.tab_id,
                    streaming_speed
                ):
                    yield text_event
            
            # Process the message with real-time streaming
            response = await self.agent.process_message_with_realtime_streaming(request, streaming_callback)
            
            # Log response details for debugging
            logger.info(f"=" * 80)
            logger.info(f"🔍 REALTIME STREAMING SERVICE - Received response from agent")
            logger.info(f"Response hotelSearch is None: {response.hotelSearch is None}")
            logger.info(f"Response webSearch is None: {response.webSearch is None}")
            logger.info(f"Intermediate text queue length: {len(intermediate_text_queue)}")
            logger.info(f"=" * 80)
            
            # Small delay after intermediate streaming to let it render before structured results
            await asyncio.sleep(0.3)
            
            # Stream hotel results after intermediate text streaming
            if response.hotelSearch:
                logger.info(f"🏨 Sending hotel results: {response.hotelSearch.resultsTitle}")
                logger.info(f"🏨 Hotel results count: {len(response.hotelSearch.results)}")
                
                hotel_data = {
                    "resultsTitle": response.hotelSearch.resultsTitle,
                    "results": [
                        {
                            "id": hotel.id,
                            "name": hotel.name,
                            "link": hotel.link,
                            "description": hotel.description,
                            "rating": hotel.rating,
                            "reviews": hotel.reviews,
                            "stars": hotel.stars,
                            "address": hotel.address,
                            "phone": hotel.phone,
                            "features": hotel.features,
                            "price": hotel.price,
                            "priceLabel": hotel.priceLabel,
                            "roomType": hotel.roomType,
                            "source": hotel.source,
                            "sourceUrl": hotel.sourceUrl,
                            "imageUrls": hotel.imageUrls,
                            "aiNote": hotel.aiNote,
                            "position": {
                                "lat": hotel.position.lat,
                                "lng": hotel.position.lng
                            } if hotel.position else None,
                            "extra_prices": [
                                {
                                    "source": extra_price.source,
                                    "source_url": extra_price.source_url,
                                    "price": extra_price.price
                                }
                                for extra_price in hotel.extra_prices
                            ] if hotel.extra_prices else None
                        }
                        for hotel in response.hotelSearch.results
                    ]
                }
                
                hotel_event = HotelResultsEvent(
                    session_id=session_id,
                    tab_id=request.tab_id,
                    hotel_search=hotel_data
                )
                logger.info(f"🏨 Generated hotel event - session: {session_id}, tab: {request.tab_id}")
                yield hotel_event
            
            # Stream web search results if available (independent of hotel results)
            if response.webSearch:
                logger.info(f"🌐 Processing web search results...")
                web_data = {
                    "resultsTitle": response.webSearch.resultsTitle,
                    "images": [
                        {
                            "url": img.url,
                            "description": img.description
                        }
                        for img in response.webSearch.images
                    ]
                }
                
                logger.info(f"🌐 Web data prepared - {len(web_data['images'])} images")
                yield WebResultsEvent(
                    session_id=session_id,
                    tab_id=request.tab_id,
                    web_search=web_data
                )
            
            # Send suggestions
            if response.suggestions:
                yield SuggestionsEvent(
                    session_id=session_id,
                    tab_id=request.tab_id,
                    suggestions=response.suggestions
                )
            
            # Store the assistant's final summary text and structured results
            message_content = response.message or "No message content"
            
            # Prepare metadata with structured results
            metadata = {}
            if response.hotelSearch:
                metadata["hotelSearch"] = {
                    "resultsTitle": response.hotelSearch.resultsTitle,
                    "results": [
                        {
                            "id": hotel.id,
                            "name": hotel.name,
                            "link": hotel.link,
                            "description": hotel.description,
                            "rating": hotel.rating,
                            "reviews": hotel.reviews,
                            "stars": hotel.stars,
                            "address": hotel.address,
                            "phone": hotel.phone,
                            "features": hotel.features,
                            "price": hotel.price,
                            "priceLabel": hotel.priceLabel,
                            "roomType": hotel.roomType,
                            "source": hotel.source,
                            "sourceUrl": hotel.sourceUrl,
                            "imageUrls": hotel.imageUrls,
                            "aiNote": hotel.aiNote,
                            "position": {
                                "lat": hotel.position.lat,
                                "lng": hotel.position.lng
                            } if hotel.position else None,
                            "extra_prices": [
                                {
                                    "source": extra_price.source,
                                    "source_url": extra_price.source_url,
                                    "price": extra_price.price
                                }
                                for extra_price in hotel.extra_prices
                            ] if hotel.extra_prices else None
                        }
                        for hotel in response.hotelSearch.results
                    ]
                }
            
            if response.webSearch:
                metadata["webSearch"] = {
                    "resultsTitle": response.webSearch.resultsTitle,
                    "images": [
                        {
                            "url": img.url,
                            "description": img.description
                        }
                        for img in response.webSearch.images
                    ]
                }
            
            # Store the assistant's response in memory
            await self.hybrid_memory.add_assistant_message(
                session_id, 
                message_content, 
                metadata=metadata
            )
            
            # Send completion event
            yield CompleteEvent(
                session_id=session_id,
                tab_id=request.tab_id,
                final_message=message_content,
                metadata={
                    "realtime_streaming": True,
                    "intermediate_responses_count": len(intermediate_text_queue)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in realtime streaming chat processing: {e}")
            
            # Send error event
            yield ErrorEvent(
                session_id=request.session_id or str(uuid.uuid4()),
                tab_id=request.tab_id,
                error_message=f"Error processing request: {str(e)}",
                error_code="REALTIME_STREAMING_ERROR"
            )

    async def close(self):
        """Clean up resources"""
        await self.agent.close()
