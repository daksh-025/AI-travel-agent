from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from typing import List, Optional
from app.chat.models import ChatRequest, ChatResponse, ChatSession, CreateTabRequest, UpdateTabRequest, TabResponse
from app.chat.response_models import StructuredChatResponse
from app.chat.streaming_models import StreamingChatRequest
from app.chat.service import ChatService
from app.dependencies import get_db, get_current_user, get_current_user_optional
from app.models import UserInDB
from app.middleware.rate_limit import check_rate_limit_for_guests, get_rate_limit_info
from motor.motor_asyncio import AsyncIOMotorDatabase
import json
import asyncio

router = APIRouter(prefix="/chat", tags=["chat"])


def get_chat_service(db: AsyncIOMotorDatabase = Depends(get_db)) -> ChatService:
    """Dependency to get chat service instance"""
    return ChatService(db)


@router.post("/message", response_model=StructuredChatResponse)
async def send_message(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
    current_user: Optional[UserInDB] = Depends(get_current_user_optional),
    _rate_limit_check: None = Depends(check_rate_limit_for_guests)
):
    """
    Send a message to the hotel AI chat assistant
    
    This endpoint processes user messages and returns AI responses.
    The AI can access hotel information, make bookings, provide travel advice,
    and answer questions using various tools including:
    - Database search for hotel information
    - API calls for external services
    - Web scraping for real-time information
    - Vector search for similar content
    
    For new conversations (first message in a tab), the system will automatically
    suggest a relevant tab name based on the user's message using AI.
    
    **Rate Limiting for Non-Authenticated Users:**
    - Guest users are limited to 3 chat requests per day
    - Rate limits reset at midnight UTC
    - Authenticated users have unlimited access
    """
    try:
        user_id = current_user.id if current_user else None
        response = await chat_service.process_chat_message(request, user_id)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat message: {str(e)}"
        )


@router.post("/message/stream")
async def send_message_stream(
    request: StreamingChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
    current_user: Optional[UserInDB] = Depends(get_current_user_optional),
    _rate_limit_check: None = Depends(check_rate_limit_for_guests)
):
    """
    Send a message to the hotel AI chat assistant with streaming response
    
    This endpoint processes user messages and returns AI responses using Server-Sent Events (SSE).
    The response includes:
    - Real-time progress indicators showing search phases
    - Word-by-word text streaming for natural conversation feel
    - Structured data (hotel results, web search results) when applicable
    - AI-generated suggestions for follow-up questions
    
    The streaming includes progress phases like:
    - Searching booking.com...
    - Checking Google hotels...
    - Analyzing 150 other accommodation sites...
    - Thinking about your specific preferences...
    - Matching you to the best options...
    
    **Rate Limiting for Non-Authenticated Users:**
    - Guest users are limited to 3 chat requests per day
    - Rate limits reset at midnight UTC
    - Authenticated users have unlimited access
    """
    
    async def generate_stream():
        """Generate the Server-Sent Events stream"""
        try:
            user_id = current_user.id if current_user else None
            
            # Convert streaming request to regular chat request
            chat_request = ChatRequest(
                message=request.message,
                session_id=request.session_id,
                tab_id=request.tab_id,
                context=request.context
            )
            
            # Process the message with streaming support
            async for event in chat_service.process_chat_message_stream(
                chat_request, 
                user_id, 
                enable_progress=request.enable_progress,
                streaming_speed=request.streaming_speed
            ):
                # Format as Server-Sent Event
                event_data = event.model_dump_json()
                yield f"data: {event_data}\n\n"
                
                # Small delay to ensure proper streaming
                await asyncio.sleep(0.01)
            
        except Exception as e:
            # Send error event
            error_event = {
                "event_type": "error",
                "error_message": f"Error processing chat message: {str(e)}",
                "timestamp": "2024-01-01T00:00:00Z",
                "session_id": request.session_id or "unknown"
            }
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


@router.post("/tabs", response_model=TabResponse)
async def create_new_tab(
    request: CreateTabRequest,
    chat_service: ChatService = Depends(get_chat_service),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Create a new chat tab for the authenticated user
    
    Creates a new tab with an associated session. The tab can be used
    for a new conversation thread.
    """
    try:
        tab = await chat_service.create_new_tab(current_user.id, request.title)
        return TabResponse(
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating new tab: {str(e)}"
        )


@router.get("/tabs", response_model=List[TabResponse])
async def get_user_tabs(
    chat_service: ChatService = Depends(get_chat_service),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get all chat tabs for the authenticated user
    
    Returns a list of all user's chat tabs ordered by last activity.
    Each tab represents a separate conversation thread.
    """
    try:
        tabs = await chat_service.get_user_tabs(current_user.id)
        return tabs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user tabs: {str(e)}"
        )


@router.put("/tabs/{tab_id}")
async def update_tab(
    tab_id: str,
    request: UpdateTabRequest,
    chat_service: ChatService = Depends(get_chat_service),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Update a chat tab
    
    Allows updating the tab title, pinned status, and order index.
    Only the tab owner can update their tabs.
    """
    try:
        success = await chat_service.update_tab(tab_id, current_user.id, request)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tab not found or access denied"
            )
        
        return {"message": "Tab updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating tab: {str(e)}"
        )


@router.delete("/tabs/{tab_id}")
async def delete_tab(
    tab_id: str,
    chat_service: ChatService = Depends(get_chat_service),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Delete a chat tab and its associated session
    
    Permanently deletes the tab and all its conversation history.
    Only the tab owner can delete their tabs.
    """
    try:
        success = await chat_service.delete_tab(tab_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tab not found or access denied"
            )
        
        return {"message": "Tab deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting tab: {str(e)}"
        )


@router.get("/history/{session_id}")
async def get_conversation_history(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service),
    current_user: Optional[UserInDB] = Depends(get_current_user_optional)
):
    """
    Get conversation history for a specific session
    
    Returns the full conversation history including both user and AI messages.
    For authenticated users, validates session ownership.
    """
    try:
        user_id = current_user.id if current_user else None
        history = await chat_service.get_conversation_history(session_id, user_id)
        return {
            "session_id": session_id,
            "messages": history,
            "message_count": len(history)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving conversation history: {str(e)}"
        )


@router.delete("/history/{session_id}")
async def clear_conversation(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service),
    current_user: Optional[UserInDB] = Depends(get_current_user_optional)
):
    """
    Clear conversation history for a specific session
    
    Permanently deletes all messages in the conversation.
    For authenticated users, validates session ownership.
    """
    try:
        user_id = current_user.id if current_user else None
        success = await chat_service.clear_conversation(session_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied"
            )
        
        return {"message": "Conversation history cleared successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing conversation: {str(e)}"
        )


@router.get("/sessions", response_model=List[ChatSession])
async def get_user_sessions(
    chat_service: ChatService = Depends(get_chat_service),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get all chat sessions for the authenticated user
    
    Returns a list of all active chat sessions with metadata.
    Requires authentication.
    """
    try:
        sessions = await chat_service.get_user_sessions(current_user.id)
        return sessions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user sessions: {str(e)}"
        )


@router.get("/stats/{session_id}")
async def get_session_stats(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service),
    current_user: Optional[UserInDB] = Depends(get_current_user_optional)
):
    """
    Get statistics for a specific session
    
    Returns detailed statistics about the conversation session.
    For authenticated users, validates session ownership.
    """
    try:
        user_id = current_user.id if current_user else None
        stats = await chat_service.get_session_stats(session_id)
        return {
            "session_id": session_id,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving session stats: {str(e)}"
        )


@router.delete("/history/user/all")
async def clear_all_user_history(
    chat_service: ChatService = Depends(get_chat_service),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Clear all chat history for the authenticated user
    
    Permanently deletes all messages, sessions, and tabs for the user.
    This is a destructive operation that cannot be undone.
    Requires authentication.
    """
    try:
        success = await chat_service.clear_all_user_history(current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to clear user history"
            )
        
        return {"message": "All user chat history cleared successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing user history: {str(e)}"
        )


@router.get("/rate-limit")
async def get_rate_limit_status(
    rate_limit_info: dict = Depends(get_rate_limit_info)
):
    """
    Get current rate limit status for the user
    
    Returns usage information including:
    - Number of requests made today
    - Total daily limit
    - Remaining requests
    - When the limit resets
    
    For authenticated users, returns unlimited status.
    For guest users, returns detailed usage information.
    """
    return rate_limit_info


@router.get("/health")
async def chat_health_check():
    """
    Health check endpoint for the chat service
    
    Returns the status of the chat system and available tools.
    """
    return {
        "status": "healthy",
        "service": "hotel-chat-ai",
        "features": [
            "LangChain integration",
            "Hybrid memory (Redis + MongoDB)",
            "API calls",
            "Web scraping",
            "Vector search (Pinecone)",
            "Conversation memory",
            "Session management",
            "Chat tabs management",
            "Rate limiting for guests"
        ],
        "tools_available": [
            "mongodb_retrieve",
            "api_call", 
            "web_scraper",
            "pinecone_retrieve"
        ],
        "memory_system": "hybrid_redis_mongodb"
    }
