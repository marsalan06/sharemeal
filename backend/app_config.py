from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import connect_to_mongo, close_mongo_connection
import logging

logger = logging.getLogger(__name__)


def setup_app(app: FastAPI):
    """Configure CORS middleware"""
    logger.info("Setting up CORS middleware")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def setup_events(app: FastAPI):
    """Setup startup and shutdown events"""
    @app.on_event("startup")
    async def startup_event():
        logger.info("Application startup - connecting to MongoDB")
        await connect_to_mongo()
        logger.info("Application startup complete")

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Application shutdown - closing MongoDB connection")
        await close_mongo_connection()
        logger.info("Application shutdown complete")

