"""
Rate limiting service for non-authenticated users.
Uses Redis to track usage with daily resets.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
import redis.asyncio as redis
from app.core.config import settings


class RateLimitService:
    """Service for managing rate limits for non-authenticated users"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.daily_limit = 10  # Number of requests allowed per day
        
    def _get_rate_limit_key(self, identifier: str) -> str:
        """Generate Redis key for rate limiting"""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return f"rate_limit:guest:{identifier}:{today}"
    
    def _get_seconds_until_midnight(self) -> int:
        """Calculate seconds until midnight UTC"""
        now = datetime.now(timezone.utc)
        midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return int((midnight - now).total_seconds())
    
    async def check_rate_limit(self, identifier: str) -> tuple[bool, int, int]:
        """
        Check if the user has exceeded their rate limit.
        
        Args:
            identifier: Unique identifier for the user (e.g., IP address)
            
        Returns:
            tuple: (is_allowed, current_usage, remaining_requests)
                - is_allowed: True if request is allowed, False if limit exceeded
                - current_usage: Number of requests made today
                - remaining_requests: Number of requests remaining
        """
        key = self._get_rate_limit_key(identifier)
        
        # Get current usage count
        current_usage = await self.redis_client.get(key)
        current_usage = int(current_usage) if current_usage else 0
        
        # Check if limit exceeded
        is_allowed = current_usage < self.daily_limit
        remaining = max(0, self.daily_limit - current_usage)
        
        return is_allowed, current_usage, remaining
    
    async def increment_usage(self, identifier: str) -> int:
        """
        Increment the usage counter for a user.
        
        Args:
            identifier: Unique identifier for the user
            
        Returns:
            int: New usage count
        """
        key = self._get_rate_limit_key(identifier)
        
        # Increment counter
        new_count = await self.redis_client.incr(key)
        
        # Set expiration to midnight if this is the first request of the day
        if new_count == 1:
            seconds_until_midnight = self._get_seconds_until_midnight()
            await self.redis_client.expire(key, seconds_until_midnight)
        
        return new_count
    
    async def get_usage_info(self, identifier: str) -> dict:
        """
        Get detailed usage information for a user.
        
        Args:
            identifier: Unique identifier for the user
            
        Returns:
            dict: Usage information including count, limit, remaining, and reset time
        """
        key = self._get_rate_limit_key(identifier)
        
        current_usage = await self.redis_client.get(key)
        current_usage = int(current_usage) if current_usage else 0
        
        ttl = await self.redis_client.ttl(key)
        reset_time = None
        if ttl > 0:
            reset_time = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        
        return {
            "usage": current_usage,
            "limit": self.daily_limit,
            "remaining": max(0, self.daily_limit - current_usage),
            "reset_at": reset_time.isoformat() if reset_time else None,
            "reset_in_seconds": ttl if ttl > 0 else None
        }
    
    async def reset_usage(self, identifier: str) -> bool:
        """
        Manually reset usage for a user (admin function).
        
        Args:
            identifier: Unique identifier for the user
            
        Returns:
            bool: True if reset was successful
        """
        key = self._get_rate_limit_key(identifier)
        deleted = await self.redis_client.delete(key)
        return deleted > 0

