from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from enum import Enum


class StreamingEventType(str, Enum):
    """Types of streaming events"""
    PROGRESS = "progress"
    TEXT_CHUNK = "text_chunk"
    HOTEL_RESULTS = "hotel_results"
    WEB_RESULTS = "web_results"
    SUGGESTIONS = "suggestions"
    COMPLETE = "complete"
    ERROR = "error"


class ProgressPhase(str, Enum):
    """Different phases of the search/processing"""
    STARTING = "starting"
    SEARCHING_BOOKING = "searching_booking"
    CHECKING_GOOGLE = "checking_google"
    ANALYZING_SITES = "analyzing_sites"
    THINKING_PREFERENCES = "thinking_preferences"
    MATCHING_OPTIONS = "matching_options"
    GENERATING_RESPONSE = "generating_response"
    COMPLETE = "complete"


class ProgressUpdate(BaseModel):
    """Progress indicator update"""
    phase: ProgressPhase = Field(..., description="Current processing phase")
    message: str = Field(..., description="Human-readable progress message")
    percentage: Optional[int] = Field(None, description="Progress percentage (0-100)")
    details: Optional[str] = Field(None, description="Additional details about current phase")


class TextChunk(BaseModel):
    """Individual text chunk for word-by-word streaming"""
    content: str = Field(..., description="Text content (word or phrase)")
    is_complete_word: bool = Field(True, description="Whether this is a complete word")
    is_formatting: bool = Field(False, description="Whether this is a formatting character (\\n, \\t, etc.)")
    formatting_type: Optional[str] = Field(None, description="Type of formatting: 'newline', 'tab', 'space', etc.")
    delay_ms: Optional[int] = Field(None, description="Suggested delay before next chunk")


class StreamingEvent(BaseModel):
    """Base streaming event model"""
    event_type: StreamingEventType = Field(..., description="Type of streaming event")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: str = Field(..., description="Session identifier")
    tab_id: Optional[str] = Field(None, description="Tab identifier if applicable")


class ProgressEvent(StreamingEvent):
    """Progress update event"""
    event_type: StreamingEventType = Field(default=StreamingEventType.PROGRESS)
    progress: ProgressUpdate = Field(..., description="Progress information")


class TextChunkEvent(StreamingEvent):
    """Text chunk streaming event"""
    event_type: StreamingEventType = Field(default=StreamingEventType.TEXT_CHUNK)
    chunk: TextChunk = Field(..., description="Text chunk data")
    is_final_chunk: bool = Field(False, description="Whether this is the last chunk")


class HotelResultsEvent(StreamingEvent):
    """Hotel results streaming event"""
    event_type: StreamingEventType = Field(default=StreamingEventType.HOTEL_RESULTS)
    hotel_search: Dict[str, Any] = Field(..., description="Hotel search results")


class WebResultsEvent(StreamingEvent):
    """Web results streaming event"""
    event_type: StreamingEventType = Field(default=StreamingEventType.WEB_RESULTS)
    web_search: Dict[str, Any] = Field(..., description="Web search results")


class SuggestionsEvent(StreamingEvent):
    """Suggestions streaming event"""
    event_type: StreamingEventType = Field(default=StreamingEventType.SUGGESTIONS)
    suggestions: List[str] = Field(..., description="AI-generated suggestions")


class CompleteEvent(StreamingEvent):
    """Completion event"""
    event_type: StreamingEventType = Field(default=StreamingEventType.COMPLETE)
    final_message: str = Field(..., description="Final complete message")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ErrorEvent(StreamingEvent):
    """Error event"""
    event_type: StreamingEventType = Field(default=StreamingEventType.ERROR)
    error_message: str = Field(..., description="Error description")
    error_code: Optional[str] = Field(None, description="Error code if applicable")


class StreamingChatRequest(BaseModel):
    """Request model for streaming chat"""
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session identifier")
    tab_id: Optional[str] = Field(None, description="Tab identifier")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    enable_progress: bool = Field(True, description="Whether to send progress updates")
    streaming_speed: Literal["fast", "normal", "slow"] = Field("normal", description="Text streaming speed")
