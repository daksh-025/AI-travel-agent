import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from app.repositories.chat_repository import ChatRepository
from app.models.chat import ChatMessage, ChatSession, ChatTab
from app.core.config import settings

logger = logging.getLogger(__name__)


class HybridMemoryService:
    """Hybrid memory service combining Redis (LangChain) and MongoDB (persistent storage)"""
    
    def __init__(self, chat_repository: ChatRepository):
        self.chat_repository = chat_repository
    
    
    def create_conversation_memory(
        self, 
        session_id: str, 
        return_messages: bool = False
    ) -> ConversationBufferMemory:
        """
        Create a conversation memory instance with Redis backend
        
        Args:
            session_id: Unique identifier for the conversation session
            return_messages: Whether to return messages or string format
            
        Returns:
            ConversationMemory instance
        """
        # Create Redis-backed chat message history
        chat_history = RedisChatMessageHistory(
            session_id=session_id,
            url=settings.redis_url,
        )
        
        # Buffer memory - stores all messages
        memory = ConversationBufferMemory(
            chat_memory=chat_history,
            return_messages=return_messages,
            input_key="input",
            output_key="output"
        )
        
        return memory
    
    async def get_conversation_history(self, session_id: str, limit: int = 20) -> List[BaseMessage]:
        """
        Get conversation history for a session from Redis (LangChain format)
        Limited to the most recent messages
        
        Args:
            session_id: Session identifier
            limit: Maximum number of recent messages to return (default: 20)
            
        Returns:
            List of LangChain BaseMessage objects (limited to most recent)
        """
        try:
            chat_history = RedisChatMessageHistory(
                session_id=session_id,
                url=settings.redis_url,
            )
            
            # Get all messages and return only the most recent ones
            all_messages = chat_history.messages
            return all_messages[-limit:] if len(all_messages) > limit else all_messages
        except Exception as e:
            logger.error(f"Error retrieving conversation history from Redis for session {session_id}: {e}")
            # Fallback to MongoDB if Redis fails
            return await self._get_history_from_mongodb(session_id, limit)
    
    async def _get_history_from_mongodb(self, session_id: str, limit: int = 20) -> List[BaseMessage]:
        """Fallback method to get history from MongoDB and convert to LangChain format"""
        try:
            messages = await self.chat_repository.get_messages_by_session(session_id, limit=limit)
            langchain_messages = []
            
            for msg in messages:
                if msg.role == "user":
                    langchain_messages.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    # Include metadata in assistant messages for structured data
                    ai_message = AIMessage(content=msg.content)
                    if msg.metadata:
                        # Add metadata as additional_kwargs for structured data
                        ai_message.additional_kwargs = {"metadata": msg.metadata}
                    langchain_messages.append(ai_message)
            
            return langchain_messages
        except Exception as e:
            logger.error(f"Error getting history from MongoDB for session {session_id}: {e}")
            return []
    
    async def get_full_conversation_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get full conversation history with metadata from MongoDB
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return
            
        Returns:
            List of message dictionaries with metadata
        """
        try:
            messages = await self.chat_repository.get_messages_by_session(session_id, limit=limit)
            full_messages = []
            
            for msg in messages:
                message_dict = {
                    "id": str(msg.id),
                    "session_id": msg.session_id,
                    "user_id": msg.user_id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "metadata": msg.metadata
                }
                full_messages.append(message_dict)
            
            return full_messages
        except Exception as e:
            logger.error(f"Error getting full conversation history for session {session_id}: {e}")
            return []
    
    async def add_user_message(self, session_id: str, message: str, user_id: Optional[str] = None) -> bool:
        """
        Add a user message to both Redis and MongoDB
        
        Args:
            session_id: Session identifier
            message: User message content
            user_id: Optional user ID for authenticated users
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Add to Redis (LangChain)
            chat_history = RedisChatMessageHistory(
                session_id=session_id,
                url=settings.redis_url,
            )
            chat_history.add_user_message(message)
            
            # Add to MongoDB (persistent storage)
            chat_message = ChatMessage(
                session_id=session_id,
                user_id=user_id,
                role="user",
                content=message,
                timestamp=datetime.utcnow()
            )
            await self.chat_repository.create_message(chat_message)
            
            # Update session activity
            await self._update_session_activity(session_id, user_id)
            
            return True
        except Exception as e:
            logger.error(f"Error adding user message for session {session_id}: {e}")
            return False
    
    async def add_ai_message(self, session_id: str, message: str, user_id: Optional[str] = None) -> bool:
        """
        Add an AI message to both Redis and MongoDB
        
        Args:
            session_id: Session identifier
            message: AI message content
            user_id: Optional user ID for authenticated users
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Add to Redis (LangChain)
            chat_history = RedisChatMessageHistory(
                session_id=session_id,
                url=settings.redis_url,
            )
            chat_history.add_ai_message(message)
            
            # Add to MongoDB (persistent storage)
            chat_message = ChatMessage(
                session_id=session_id,
                user_id=user_id,
                role="assistant",
                content=message,
                timestamp=datetime.utcnow()
            )
            await self.chat_repository.create_message(chat_message)
            
            # Update session activity
            await self._update_session_activity(session_id, user_id)
            
            return True
        except Exception as e:
            logger.error(f"Error adding AI message for session {session_id}: {e}")
            return False
    
    async def add_ai_message_with_metadata(self, session_id: str, message: str, metadata: Dict[str, Any], user_id: Optional[str] = None) -> bool:
        """
        Add an AI message with structured metadata to both Redis and MongoDB
        
        Args:
            session_id: Session identifier
            message: AI message content
            metadata: Structured data (hotel results, web search results, etc.)
            user_id: Optional user ID for authenticated users
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Add to Redis (LangChain) - only the text message
            chat_history = RedisChatMessageHistory(
                session_id=session_id,
                url=settings.redis_url,
            )
            chat_history.add_ai_message(message)
            
            # Add to MongoDB (persistent storage) with metadata
            chat_message = ChatMessage(
                session_id=session_id,
                user_id=user_id,
                role="assistant",
                content=message,
                metadata=metadata,
                timestamp=datetime.utcnow()
            )
            await self.chat_repository.create_message(chat_message)
            
            # Update session activity
            await self._update_session_activity(session_id, user_id)
            
            return True
        except Exception as e:
            logger.error(f"Error adding AI message with metadata for session {session_id}: {e}")
            return False
    
    async def _update_session_activity(self, session_id: str, user_id: Optional[str] = None):
        """Update session activity and create session if it doesn't exist"""
        try:
            # Check if session exists
            existing_session = await self.chat_repository.get_session(session_id)
            
            if existing_session:
                # Update existing session
                await self.chat_repository.update_session_activity(session_id)
            else:
                # Create new session
                new_session = ChatSession(
                    session_id=session_id,
                    user_id=user_id,
                    created_at=datetime.utcnow(),
                    last_activity=datetime.utcnow(),
                    message_count=0,
                    is_active=True
                )
                await self.chat_repository.create_session(new_session)
                
                # If user_id is provided, also update the associated tab
                if user_id:
                    tab = await self.chat_repository.get_tab_by_session(session_id)
                    if tab:
                        await self.chat_repository.update_tab_activity(tab.tab_id)
        except Exception as e:
            logger.error(f"Error updating session activity for {session_id}: {e}")
    
    async def clear_conversation_history(self, session_id: str) -> bool:
        """
        Clear conversation history for a session from both Redis and MongoDB
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Clear from Redis
            chat_history = RedisChatMessageHistory(
                session_id=session_id,
                url=settings.redis_url,
            )
            chat_history.clear()
            
            # Clear from MongoDB
            await self.chat_repository.delete_messages_by_session(session_id)
            await self.chat_repository.delete_conversation_history(session_id)
            
            logger.info(f"Cleared conversation history for session: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing conversation history for session {session_id}: {e}")
            return False
    
    async def get_mongodb_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get conversation history from MongoDB in a serializable format
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of message dictionaries with parsed structured content
        """
        try:
            import json
            messages = await self.chat_repository.get_messages_by_session(session_id)
            formatted_messages = []
            
            for msg in messages:
                message_data = {
                    "role": msg.role,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata
                }
                
                # Check if metadata contains structured data (hotel results, web search results)
                if msg.metadata:
                    if "hotelSearch" in msg.metadata:
                        message_data["hotelSearch"] = msg.metadata["hotelSearch"]
                    if "webSearch" in msg.metadata:
                        message_data["webSearch"] = msg.metadata["webSearch"]
                
                # Try to parse structured content if it's JSON
                try:
                    parsed_content = json.loads(msg.content)
                    if isinstance(parsed_content, dict):
                        if parsed_content.get("type") == "hotel_search":
                            # This is a structured hotel search response
                            message_data["content"] = parsed_content.get("content", "")
                            message_data["hotelSearch"] = {
                                "resultsTitle": parsed_content.get("resultsTitle", ""),
                                "results": parsed_content.get("results", [])
                            }
                        elif parsed_content.get("type") == "web_search":
                            # This is a structured web search response
                            message_data["content"] = parsed_content.get("content", "")
                            message_data["webSearch"] = {
                                "resultsTitle": parsed_content.get("resultsTitle", ""),
                                "images": parsed_content.get("images", [])
                            }
                        else:
                            # Regular content
                            message_data["content"] = msg.content
                    else:
                        # Regular content
                        message_data["content"] = msg.content
                except (json.JSONDecodeError, TypeError):
                    # Regular text content
                    message_data["content"] = msg.content
                
                formatted_messages.append(message_data)
            
            return formatted_messages
        except Exception as e:
            logger.error(f"Error getting MongoDB history for session {session_id}: {e}")
            return []
    
    async def get_user_sessions(self, user_id: str) -> List[ChatSession]:
        """
        Get all sessions for a user from MongoDB
        
        Args:
            user_id: User identifier
            
        Returns:
            List of chat sessions
        """
        try:
            return await self.chat_repository.get_user_sessions(user_id)
        except Exception as e:
            logger.error(f"Error getting user sessions for {user_id}: {e}")
            return []

    async def get_user_tabs(self, user_id: str) -> List[ChatTab]:
        """
        Get all tabs for a user from MongoDB
        
        Args:
            user_id: User identifier
            
        Returns:
            List of chat tabs
        """
        try:
            return await self.chat_repository.get_user_tabs(user_id)
        except Exception as e:
            logger.error(f"Error getting user tabs for {user_id}: {e}")
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
            return await self.chat_repository.get_session_stats(session_id)
        except Exception as e:
            logger.error(f"Error getting session stats for {session_id}: {e}")
            return {}

    async def clear_all_user_memory(self, user_id: str) -> bool:
        """
        Clear all Redis memory for a user's sessions
        
        Args:
            user_id: User identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all user sessions
            sessions = await self.chat_repository.get_user_sessions(user_id)
            
            # Clear Redis memory for each session
            cleared_count = 0
            for session in sessions:
                try:
                    await self.clear_conversation_history(session.session_id)
                    cleared_count += 1
                except Exception as e:
                    logger.warning(f"Failed to clear Redis memory for session {session.session_id}: {e}")
            
            logger.info(f"Cleared Redis memory for {cleared_count}/{len(sessions)} sessions for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing all user memory for {user_id}: {e}")
            return False
    

