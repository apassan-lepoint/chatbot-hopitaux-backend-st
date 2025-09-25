"""
Entry point for the FastAPI application.
"""
import uvicorn
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.utility.functions.logging import get_logger




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
        description=(
            "API for the hospital ranking chatbot.\n\n"
            "Endpoints:\n"
            "- **/ask**: Single-turn Q&A\n"
            "- **/chat**: Multi-turn conversations\n\n"
        ),
        version="1.0.0", 
        contact={
            "name": "Chatbot Hôpitaux Support",
            "email": "apassan@ext.lepoint.fr"
        },
        docs_url="/docs", # Swagger UI
        redoc_url="/redoc", # ReDoc documentation
        openapi_url="/openapi.json" # OpenAPI schema URL
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
if __name__ == "__main__":
    logger.info("Starting server process...")
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Running app on port {port}")
    # Run the application using uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
