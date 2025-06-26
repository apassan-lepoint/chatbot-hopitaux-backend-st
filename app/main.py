"""
Entry point for the FastAPI application.

This file creates and configures the FastAPI app, sets up CORS middleware,
    and includes all API routes for the hospital ranking chatbot backend.
""" 

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Sets up the FastAPI app with metadata, enables CORS middleware for cross-origin requests,
    and includes the API routes.

    Args: 
        None
    Returns:
        FastAPI: Configured FastAPI application instance.
    """

    app = FastAPI(
        title="Chatbot Hôpitaux",
        description="API for hospital ranking chatbot",
        version="1.0.0"
    )

    # Add CORS middleware to allow frontend-backend communication
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins; restrict in production!
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Include API routes from the router
    app.include_router(router)
    return app

# Instantiate the FastAPI app
app = create_app()
