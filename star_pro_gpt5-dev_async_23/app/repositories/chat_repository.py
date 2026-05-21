import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.chat import ChatMessage, ChatSession, ConversationHistory, ChatTab
from bson import ObjectId
import uuid

logger = logging.getLogger(__name__)


class ChatRepository:
    """Repository for managing chat data in MongoDB"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.messages_collection = db.chat_messages
        self.sessions_collection = db.chat_sessions
        self.conversations_collection = db.conversation_history
        self.tabs_collection = db.chat_tabs
    
    async def create_message(self, message: ChatMessage) -> ChatMessage:
        """Create a new chat message"""
        try:
            message_dict = message.dict(by_alias=True)
            result = await self.messages_collection.insert_one(message_dict)
            message.id = result.inserted_id
            return message
        except Exception as e:
            logger.error(f"Error creating message: {e}")
            raise
    
    async def get_messages_by_session(self, session_id: str, limit: Optional[int] = None) -> List[ChatMessage]:
        """Get all messages for a session, optionally limited to most recent"""
        try:
            query = {"session_id": session_id}
            
            if limit:
                # Get the most recent messages by sorting in descending order
                cursor = self.messages_collection.find(query).sort("timestamp", -1).limit(limit)
                messages = []
                async for doc in cursor:
                    messages.append(ChatMessage(**doc))
                # Reverse to maintain chronological order (oldest to newest)
                return list(reversed(messages))
            else:
                # Get all messages in chronological order
                cursor = self.messages_collection.find(query).sort("timestamp", 1)
                messages = []
                async for doc in cursor:
                    messages.append(ChatMessage(**doc))
                return messages
        except Exception as e:
            logger.error(f"Error getting messages for session {session_id}: {e}")
            return []
    
    async def delete_messages_by_session(self, session_id: str) -> bool:
        """Delete all messages for a session"""
        try:
            result = await self.messages_collection.delete_many({"session_id": session_id})
            logger.info(f"Deleted {result.deleted_count} messages for session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting messages for session {session_id}: {e}")
            return False
    
    async def create_session(self, session: ChatSession) -> ChatSession:
        """Create a new chat session"""
        try:
            session_dict = session.dict(by_alias=True)
            result = await self.sessions_collection.insert_one(session_dict)
            session.id = result.inserted_id
            return session
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get a session by ID"""
        try:
            doc = await self.sessions_collection.find_one({"session_id": session_id})
            if doc:
                return ChatSession(**doc)
            return None
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None
    
    async def get_user_sessions(self, user_id: str) -> List[ChatSession]:
        """Get all sessions for a user"""
        try:
            cursor = self.sessions_collection.find({"user_id": user_id}).sort("last_activity", -1)
            sessions = []
            async for doc in cursor:
                sessions.append(ChatSession(**doc))
            return sessions
        except Exception as e:
            logger.error(f"Error getting sessions for user {user_id}: {e}")
            return []
    
    async def update_session_activity(self, session_id: str, message_count: Optional[int] = None) -> bool:
        """Update session last activity and optionally message count"""
        try:
            update_data = {"last_activity": datetime.utcnow()}
            if message_count is not None:
                update_data["message_count"] = message_count
            
            result = await self.sessions_collection.update_one(
                {"session_id": session_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating session activity for {session_id}: {e}")
            return False
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages"""
        try:
            # Delete session
            session_result = await self.sessions_collection.delete_one({"session_id": session_id})
            
            # Delete all messages for this session
            messages_result = await self.messages_collection.delete_many({"session_id": session_id})
            
            logger.info(f"Deleted session {session_id} and {messages_result.deleted_count} messages")
            return session_result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False
    
    async def create_conversation_history(self, conversation: ConversationHistory) -> ConversationHistory:
        """Create a new conversation history"""
        try:
            conversation_dict = conversation.dict(by_alias=True)
            result = await self.conversations_collection.insert_one(conversation_dict)
            conversation.id = result.inserted_id
            return conversation
        except Exception as e:
            logger.error(f"Error creating conversation history: {e}")
            raise
    
    async def get_conversation_history(self, session_id: str) -> Optional[ConversationHistory]:
        """Get conversation history for a session"""
        try:
            doc = await self.conversations_collection.find_one({"session_id": session_id})
            if doc:
                return ConversationHistory(**doc)
            return None
        except Exception as e:
            logger.error(f"Error getting conversation history for session {session_id}: {e}")
            return None
    
    async def update_conversation_history(self, session_id: str, messages: List[ChatMessage]) -> bool:
        """Update conversation history with new messages"""
        try:
            result = await self.conversations_collection.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "messages": [msg.dict(by_alias=True) for msg in messages],
                        "updated_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error updating conversation history for session {session_id}: {e}")
            return False
    
    async def delete_conversation_history(self, session_id: str) -> bool:
        """Delete conversation history for a session"""
        try:
            result = await self.conversations_collection.delete_one({"session_id": session_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting conversation history for session {session_id}: {e}")
            return False
    
    async def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a session"""
        try:
            # Count messages
            message_count = await self.messages_collection.count_documents({"session_id": session_id})
            
            # Get session info
            session = await self.get_session(session_id)
            
            # Get first and last message timestamps
            first_message = await self.messages_collection.find_one(
                {"session_id": session_id},
                sort=[("timestamp", 1)]
            )
            last_message = await self.messages_collection.find_one(
                {"session_id": session_id},
                sort=[("timestamp", -1)]
            )
            
            return {
                "session_id": session_id,
                "message_count": message_count,
                "session_created": session.created_at if session else None,
                "last_activity": session.last_activity if session else None,
                "first_message_time": first_message["timestamp"] if first_message else None,
                "last_message_time": last_message["timestamp"] if last_message else None
            }
        except Exception as e:
            logger.error(f"Error getting session stats for {session_id}: {e}")
            return {}

    # Chat Tab Methods
    async def create_tab(self, tab: ChatTab) -> ChatTab:
        """Create a new chat tab"""
        try:
            tab_dict = tab.dict(by_alias=True)
            result = await self.tabs_collection.insert_one(tab_dict)
            tab.id = result.inserted_id
            return tab
        except Exception as e:
            logger.error(f"Error creating tab: {e}")
            raise

    async def get_tab(self, tab_id: str) -> Optional[ChatTab]:
        """Get a tab by ID"""
        try:
            doc = await self.tabs_collection.find_one({"tab_id": tab_id})
            if doc:
                return ChatTab(**doc)
            return None
        except Exception as e:
            logger.error(f"Error getting tab {tab_id}: {e}")
            return None

    async def get_user_tabs(self, user_id: str) -> List[ChatTab]:
        """Get all tabs for a user, ordered by last activity"""
        try:
            cursor = self.tabs_collection.find({"user_id": user_id}).sort("last_activity", -1)
            tabs = []
            async for doc in cursor:
                tabs.append(ChatTab(**doc))
            return tabs
        except Exception as e:
            logger.error(f"Error getting tabs for user {user_id}: {e}")
            return []

    async def update_tab(self, tab_id: str, update_data: Dict[str, Any]) -> bool:
        """Update a tab"""
        try:
            update_data["last_activity"] = datetime.utcnow()
            result = await self.tabs_collection.update_one(
                {"tab_id": tab_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating tab {tab_id}: {e}")
            return False

    async def delete_tab(self, tab_id: str) -> bool:
        """Delete a tab and its associated session"""
        try:
            # Get the tab to find associated session
            tab = await self.get_tab(tab_id)
            if not tab:
                return False

            # Delete the tab
            tab_result = await self.tabs_collection.delete_one({"tab_id": tab_id})
            
            # Delete associated session and messages
            if tab.session_id:
                await self.delete_session(tab.session_id)
            
            logger.info(f"Deleted tab {tab_id} and associated session")
            return tab_result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting tab {tab_id}: {e}")
            return False

    async def update_tab_activity(self, tab_id: str, message_count: Optional[int] = None) -> bool:
        """Update tab last activity and optionally message count"""
        try:
            update_data = {"last_activity": datetime.utcnow()}
            if message_count is not None:
                update_data["message_count"] = message_count
            
            result = await self.tabs_collection.update_one(
                {"tab_id": tab_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating tab activity for {tab_id}: {e}")
            return False

    async def get_tab_by_session(self, session_id: str) -> Optional[ChatTab]:
        """Get tab by session ID"""
        try:
            doc = await self.tabs_collection.find_one({"session_id": session_id})
            if doc:
                return ChatTab(**doc)
            return None
        except Exception as e:
            logger.error(f"Error getting tab by session {session_id}: {e}")
            return None

    async def reorder_tabs(self, user_id: str, tab_orders: List[Dict[str, Any]]) -> bool:
        """Reorder tabs for a user"""
        try:
            for tab_order in tab_orders:
                await self.tabs_collection.update_one(
                    {"tab_id": tab_order["tab_id"], "user_id": user_id},
                    {"$set": {"order_index": tab_order["order_index"]}}
                )
            return True
        except Exception as e:
            logger.error(f"Error reordering tabs for user {user_id}: {e}")
            return False

    async def update_tab_title(self, tab_id: str, title: str) -> bool:
        """Update the title of a tab"""
        try:
            result = await self.tabs_collection.update_one(
                {"tab_id": tab_id},
                {"$set": {"title": title}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating tab title for {tab_id}: {e}")
            return False

    async def increment_tab_message_count(self, tab_id: str) -> bool:
        """Increment the message count for a tab"""
        try:
            result = await self.tabs_collection.update_one(
                {"tab_id": tab_id},
                {"$inc": {"message_count": 1}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error incrementing message count for tab {tab_id}: {e}")
            return False

    async def delete_all_user_data(self, user_id: str) -> Dict[str, int]:
        """
        Delete all chat data for a user (messages, sessions, tabs, conversation history)
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with counts of deleted items
        """
        try:
            # Delete all messages for the user
            messages_result = await self.messages_collection.delete_many({"user_id": user_id})
            
            # Delete all sessions for the user
            sessions_result = await self.sessions_collection.delete_many({"user_id": user_id})
            
            # Delete all tabs for the user
            tabs_result = await self.tabs_collection.delete_many({"user_id": user_id})
            
            # Delete all conversation history for the user
            conversations_result = await self.conversations_collection.delete_many({"user_id": user_id})
            
            deleted_counts = {
                "messages": messages_result.deleted_count,
                "sessions": sessions_result.deleted_count,
                "tabs": tabs_result.deleted_count,
                "conversations": conversations_result.deleted_count
            }
            
            logger.info(f"Deleted all user data for {user_id}: {deleted_counts}")
            return deleted_counts
            
        except Exception as e:
            logger.error(f"Error deleting all user data for {user_id}: {e}")
            return {"messages": 0, "sessions": 0, "tabs": 0, "conversations": 0}
