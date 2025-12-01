from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://username:password@cluster.mongodb.net/sharemeal?retryWrites=true&w=majority")

client: Optional[AsyncIOMotorClient] = None
database = None


async def connect_to_mongo():
    global client, database
    if client is None:
        logger.info("Connecting to MongoDB...")
        client = AsyncIOMotorClient(MONGODB_URL)
        database = client.sharemeal
        logger.info("Connected to MongoDB successfully")


async def close_mongo_connection():
    global client
    if client:
        logger.info("Closing MongoDB connection...")
        client.close()
        logger.info("Disconnected from MongoDB")


async def get_db():
    global database
    if database is None:
        await connect_to_mongo()
    return database

