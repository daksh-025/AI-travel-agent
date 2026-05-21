from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database import get_database
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.core.security import security_manager
from app.core.exceptions import TokenException
from app.core.redis_client import get_redis_connection
import redis.asyncio as redis

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncIOMotorDatabase:
    return await get_database()


async def get_redis_client() -> redis.Redis:
    """Dependency to get Redis client"""
    return await get_redis_connection()


def get_user_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_auth_service(user_repository: UserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(user_repository)


def get_user_service(user_repository: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(user_repository)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    token_data = security_manager.verify_token(credentials.credentials)
    if token_data is None:
        raise TokenException()
    
    user_repository = UserRepository(db)
    user = await user_repository.get_by_email(email=token_data.email)
    if user is None:
        raise TokenException()
    
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Optional authentication dependency.
    Returns the user if authenticated, None if not authenticated.
    Does not raise errors for missing credentials.
    """
    if credentials is None:
        return None
    
    try:
        token_data = security_manager.verify_token(credentials.credentials)
        if token_data is None:
            return None
        
        user_repository = UserRepository(db)
        user = await user_repository.get_by_email(email=token_data.email)
        return user
    except Exception:
        # If there's any error validating the token, just return None
        # This allows the endpoint to work for non-authenticated users
        return None
