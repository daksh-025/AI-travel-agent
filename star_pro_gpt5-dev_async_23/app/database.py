import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

logger = logging.getLogger(__name__)


class Database:
    client: AsyncIOMotorClient = None


db = Database()


async def get_database() -> AsyncIOMotorClient:
    return db.client[settings.database_name]


async def connect_to_mongo():
    if not settings.mongodb_url:
        logger.warning("MONGODB_URL not configured, skipping database connection")
        return
    
    # Simplified connection options for MongoDB Atlas
    connection_options = {
        "serverSelectionTimeoutMS": 30000,
        "connectTimeoutMS": 30000,
        "socketTimeoutMS": 30000,
        "maxPoolSize": 10,
        "minPoolSize": 1,
        "maxIdleTimeMS": 30000,
        "retryWrites": True,
        "retryReads": True,
        "w": "majority"
    }
    
    try:
        # For MongoDB Atlas, the connection string should include SSL parameters
        # Let's try without explicit SSL configuration first
        db.client = AsyncIOMotorClient(
            settings.mongodb_url,
            **connection_options
        )
        
        # Test the connection
        await db.client.admin.command('ping')
        logger.info("Connected to MongoDB successfully.")
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection():
    if db.client:
        db.client.close()
        logger.info("Disconnected from MongoDB.")
