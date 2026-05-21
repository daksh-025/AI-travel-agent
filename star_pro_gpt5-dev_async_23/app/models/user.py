from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class Location(BaseModel):
    """Location model for user preferences"""
    city: Optional[str] = ""
    country: Optional[str] = ""


class Preferences(BaseModel):
    """User preferences model for travel and accommodation"""
    adults: Optional[str] = "2"
    children: Optional[str] = "0"
    childrenAgeList: Optional[List[str]] = []
    tripType: Optional[str] = "Holiday"
    otherTripType: Optional[str] = ""
    budget: Optional[str] = ""
    budgetType: Optional[str] = "flexible"
    minStarRating: Optional[str] = "4"
    searchPreferences: Optional[List[str]] = []


class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    remember_me: Optional[bool] = False


class UserInDB(UserBase):
    id: str
    password: str
    is_active: bool = True
    language: Optional[str] = "English (AU)"
    location: Optional[Location] = None
    currency: Optional[str] = "AUD"
    preferences: Optional[Preferences] = None
    created_at: datetime
    updated_at: datetime


class User(UserBase):
    id: str
    is_active: bool
    language: Optional[str] = "English (AU)"
    location: Optional[Location] = None
    currency: Optional[str] = "AUD"
    preferences: Optional[Preferences] = None
    created_at: datetime
    updated_at: datetime


class UserProfileUpdate(BaseModel):
    """Model for updating user profile information"""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    language: Optional[str] = None
    location: Optional[Location] = None
    currency: Optional[str] = None
    preferences: Optional[Preferences] = None


class UserPasswordUpdate(BaseModel):
    """Model for updating user password"""
    current_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)


class UserProfileUpdateResponse(BaseModel):
    """Response model for profile update"""
    message: str
    user: User
