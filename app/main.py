from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

def create_app() -> FastAPI:
    """
    Objective: Create and configure a FastAPI application with CORS middleware.
    
    Input: None
    Returns: FastAPI application instance with CORS enabled for all origins.
    """

    app = FastAPI(
        title="Chatbot Hôpitaux",
        description="API for hospital ranking chatbot",
        version="1.0.0"
    )

    # CORS middleware for frontend/backend separation
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Adjust for production!
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)
    return app

app = create_app()