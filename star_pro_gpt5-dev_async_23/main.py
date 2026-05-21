from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import connect_to_mongo, close_mongo_connection
from app.core.redis_client import close_redis_pool
from app.routers import auth, users, chat, travel_preferences, cities
from app.core.config import settings
from app.core.middleware import LoggingMiddleware
from app.services.hotel_cache_service import hotel_cache_service
import logging
import asyncio

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    description="Staicey agent for hotel search and booking",
    version=settings.app_version,
    debug=settings.debug
)

# Add custom logging middleware
app.add_middleware(LoggingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(chat.router)
app.include_router(travel_preferences.router)
app.include_router(cities.router)

# Global variable to track database connection task
db_connection_task = None

# Startup and shutdown events
@app.on_event("startup")
async def startup_db_client():
    global db_connection_task
    logger.info("Starting application...")
    # Start database connection in background to avoid blocking app startup
    try:
        db_connection_task = asyncio.create_task(connect_db_with_retry())
        logger.info("Application startup initiated - database connection will be attempted in background")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        # Don't let startup errors crash the app

async def connect_db_with_retry():
    """Connect to database with retry logic"""
    max_retries = 5
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            await connect_to_mongo()
            logger.info("Connected to MongoDB successfully")
            
            # Initialize hotel cache service
            await hotel_cache_service.initialize()
            logger.info("Hotel cache service initialized successfully")
            
            return
        except Exception as e:
            logger.error(f"Failed to connect to database (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error("Failed to connect to database after all retries. Application will run without database.")
                # Don't raise the exception - let the app run without database

@app.on_event("shutdown")
async def shutdown_db_client():
    global db_connection_task
    logger.info("Shutting down application...")
    if db_connection_task and not db_connection_task.done():
        db_connection_task.cancel()
    await close_mongo_connection()
    await close_redis_pool()
    await hotel_cache_service.close()
    logger.info("Application shutdown complete")

@app.get("/")
async def root():
    return {"message": "staicey backend is running"}

@app.get("/health")
async def health_check():
    try:
        # Test database connection
        from app.database import db
        if db.client:
            await db.client.admin.command('ping')
            return {"status": "healthy", "database": "connected"}
        else:
            return {"status": "degraded", "database": "not_connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "database": "error", "error": str(e)}

@app.get("/cache/stats")
async def get_cache_stats():
    """Get hotel cache statistics"""
    try:
        stats = await hotel_cache_service.get_cache_stats()
        return {"status": "success", "cache_stats": stats}
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {"status": "error", "error": str(e)}

@app.post("/cache/cleanup")
async def cleanup_cache(days_old: int = 30):
    """Clean up old cached hotel data"""
    try:
        deleted_count = await hotel_cache_service.cleanup_old_cache(days_old)
        return {"status": "success", "deleted_count": deleted_count, "days_old": days_old}
    except Exception as e:
        logger.error(f"Failed to cleanup cache: {e}")
        return {"status": "error", "error": str(e)}
