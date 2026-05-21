"""
Redis client connection management for the application.
"""
import redis.asyncio as redis
from app.core.config import settings
from typing import Optional

# Global Redis connection pool
_redis_pool: Optional[redis.ConnectionPool] = None
_redis_client: Optional[redis.Redis] = None


async def get_redis_pool() -> redis.ConnectionPool:
    """Get or create Redis connection pool"""
    global _redis_pool
    
    if _redis_pool is None:
        _redis_pool = redis.ConnectionPool.from_url(
            settings.redis_url,
            max_connections=settings.redis_max_connections,
            decode_responses=True,  # Automatically decode bytes to strings
            socket_timeout=settings.redis_socket_timeout,
            socket_connect_timeout=settings.redis_connection_timeout,
            retry_on_timeout=settings.redis_retry_on_timeout
        )
    
    return _redis_pool


async def get_redis_connection() -> redis.Redis:
    """Get Redis client from connection pool"""
    pool = await get_redis_pool()
    return redis.Redis(connection_pool=pool)


async def close_redis_pool():
    """Close Redis connection pool (call on application shutdown)"""
    global _redis_pool, _redis_client
    
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None
    
    if _redis_pool:
        await _redis_pool.aclose()
        _redis_pool = None

