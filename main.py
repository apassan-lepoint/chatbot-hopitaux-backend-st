"""
Entry point for the FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.utility.logging import get_logger


logger = get_logger(__name__)

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application instance with necessary configurations, middleware, and routes.
    
    Returns:
        FastAPI: Configured FastAPI application instance.
    Raises:
        Exception: If there is an error during application setup.
    """
    logger.info("Creating FastAPI app")
    app = FastAPI(
        title="Chatbot Hôpitaux",
        description="API for hospital ranking chatbot",
        version="1.0.0"
    )

    # Add CORS middleware to allow frontend-backend communication
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # FIXME : restrict the origins in production and when connecting to the frontend
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("CORS middleware added")
    # Include API routes from the router
    app.include_router(router)
    logger.info("API router included")
    return app


# Instantiate the FastAPI app
app = create_app()
