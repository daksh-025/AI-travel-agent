"""
Rate limiting middleware and dependencies for FastAPI.
"""
from fastapi import Request, HTTPException, status, Depends
from typing import Optional
from app.models import UserInDB
from app.services.rate_limit_service import RateLimitService
from app.dependencies import get_redis_client, get_current_user_optional
import redis.asyncio as redis


async def get_rate_limit_service(
    redis_client: redis.Redis = Depends(get_redis_client)
) -> RateLimitService:
    """Dependency to get rate limit service instance"""
    return RateLimitService(redis_client)


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.
    Checks X-Forwarded-For header first (for proxies/load balancers),
    then X-Real-IP, and finally falls back to direct client IP.
    """
    # Check X-Forwarded-For header (for proxies, load balancers)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first one
        return forwarded_for.split(",")[0].strip()
    
    # Check X-Real-IP header (alternative proxy header)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # Fall back to direct client IP
    return request.client.host if request.client else "unknown"


async def check_rate_limit_for_guests(
    request: Request,
    current_user: Optional[UserInDB] = Depends(get_current_user_optional),
    rate_limit_service: RateLimitService = Depends(get_rate_limit_service)
):
    """
    Dependency that checks rate limits for non-authenticated users.
    Authenticated users bypass rate limiting.
    
    Raises:
        HTTPException: 429 Too Many Requests if rate limit exceeded
    """
    # Skip rate limiting for authenticated users
    if current_user:
        return
    
    # Get client identifier (IP address)
    client_ip = get_client_ip(request)
    
    # Check rate limit
    is_allowed, current_usage, remaining = await rate_limit_service.check_rate_limit(client_ip)
    
    if not is_allowed:
        # Get usage info for error message
        usage_info = await rate_limit_service.get_usage_info(client_ip)
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "message": "You have reached your daily limit of 3 free chat requests. Please sign up or log in for unlimited access.",
                "usage": usage_info["usage"],
                "limit": usage_info["limit"],
                "reset_at": usage_info["reset_at"],
                "reset_in_seconds": usage_info["reset_in_seconds"]
            }
        )
    
    # Increment usage counter
    await rate_limit_service.increment_usage(client_ip)
    
    # Add rate limit info to request headers (optional, for debugging)
    request.state.rate_limit_remaining = remaining - 1  # -1 because we're about to process this request
    request.state.rate_limit_limit = rate_limit_service.daily_limit


async def get_rate_limit_info(
    request: Request,
    current_user: Optional[UserInDB] = Depends(get_current_user_optional),
    rate_limit_service: RateLimitService = Depends(get_rate_limit_service)
) -> dict:
    """
    Dependency that returns current rate limit information without enforcing limits.
    Useful for displaying usage info to users.
    """
    # Authenticated users don't have rate limits
    if current_user:
        return {
            "type": "authenticated",
            "usage": None,
            "limit": None,
            "remaining": "unlimited",
            "reset_at": None
        }
    
    # Get client identifier and usage info
    client_ip = get_client_ip(request)
    usage_info = await rate_limit_service.get_usage_info(client_ip)
    
    return {
        "type": "guest",
        **usage_info
    }

