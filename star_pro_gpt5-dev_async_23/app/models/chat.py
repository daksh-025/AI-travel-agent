from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId
from pydantic_core import core_schema


class PyObjectId(str):
    """Custom ObjectId for Pydantic models that serializes as string"""
    
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        return core_schema.with_info_after_validator_function(
            lambda v, info: str(v) if v else None,
            core_schema.any_schema(),
            serialization=core_schema.str_schema(),
        )
    
    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        return {"type": "string", "format": "objectid"}


class ChatMessage(BaseModel):
    """MongoDB model for individual chat messages"""
    id: Optional[PyObjectId] = Field(default_factory=lambda: PyObjectId(str(ObjectId())), alias="_id")
    session_id: str = Field(..., description="Session identifier")
    user_id: Optional[str] = Field(None, description="User ID if authenticated")
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional message metadata")
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "validate_assignment": True
    }
    
    @field_validator('id', mode='before')
    @classmethod
    def validate_object_id(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            return PyObjectId(v)
        if isinstance(v, ObjectId):
            return PyObjectId(str(v))
        return v


class ChatSession(BaseModel):
    """MongoDB model for chat sessions"""
    id: Optional[PyObjectId] = Field(default_factory=lambda: PyObjectId(str(ObjectId())), alias="_id")
    session_id: str = Field(..., description="Unique session identifier")
    user_id: Optional[str] = Field(None, description="User ID if authenticated")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    message_count: int = Field(default=0, description="Total number of messages")
    is_active: bool = Field(default=True, description="Whether session is active")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Session metadata")
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "validate_assignment": True
    }
    
    @field_validator('id', mode='before')
    @classmethod
    def validate_object_id(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            return PyObjectId(v)
        if isinstance(v, ObjectId):
            return PyObjectId(str(v))
        return v


class ChatTab(BaseModel):
    """MongoDB model for chat tabs/conversations"""
    id: Optional[PyObjectId] = Field(default_factory=lambda: PyObjectId(str(ObjectId())), alias="_id")
    tab_id: str = Field(..., description="Unique tab identifier")
    user_id: str = Field(..., description="User ID who owns this tab")
    title: str = Field(default="New Chat", description="Tab title/name")
    session_id: str = Field(..., description="Associated session ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    message_count: int = Field(default=0, description="Number of messages in this tab")
    is_active: bool = Field(default=True, description="Whether tab is active")
    is_pinned: bool = Field(default=False, description="Whether tab is pinned")
    order_index: int = Field(default=0, description="Order index for tab sorting")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional tab metadata")
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "validate_assignment": True
    }
    
    @field_validator('id', mode='before')
    @classmethod
    def validate_object_id(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            return PyObjectId(v)
        if isinstance(v, ObjectId):
            return PyObjectId(str(v))
        return v


class ConversationHistory(BaseModel):
    """MongoDB model for conversation history"""
    id: Optional[PyObjectId] = Field(default_factory=lambda: PyObjectId(str(ObjectId())), alias="_id")
    session_id: str = Field(..., description="Session identifier")
    user_id: Optional[str] = Field(None, description="User ID if authenticated")
    messages: List[ChatMessage] = Field(default_factory=list, description="List of messages")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
        "validate_assignment": True
    }
    
    @field_validator('id', mode='before')
    @classmethod
    def validate_object_id(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            return PyObjectId(v)
        if isinstance(v, ObjectId):
            return PyObjectId(str(v))
        return v
