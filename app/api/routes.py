"""
routes.py
---------------------------------
Defines API endpoints for single-turn and multi-turn interactions with the hospital chatbot.
Utilizes FastAPI for routing and request handling.
"""

from fastapi import APIRouter, HTTPException
from app.config.features_config import ENABLE_MULTI_TURN
from app.pydantic_models.query_model import UserQuery, ChatRequest
from app.pydantic_models.response_model import AskResponse, ChatResponse
from app.services.conversation_service import ConversationService
from app.services.pipeline_orchestrator_service import PipelineOrchestrator
from app.utility.logging import get_logger


# Initialize logger for this module
logger = get_logger(__name__)

# Initialize the API router instance to define and group related endpoints
router = APIRouter()

# Services
conversation_service = ConversationService()
pipeline = PipelineOrchestrator()


# === Single-turn endpoint ===
@router.post(
    "/ask",
    response_model=AskResponse,
    tags=["Chatbot"],
    summary="Ask a single-turn question",
    description="Submit a one-off question about hospitals. "
                "Returns the best response and relevant hospital links."
)
def ask_question(query: UserQuery):
    """
    Handles single-turn queries using the pipeline only.
    """
    try:
        result, links = pipeline.generate_response(prompt=query.prompt, selected_specialty=getattr(query, "selected_specialty", None))
        if isinstance(result, tuple): # Defensive: unpack again if needed
            result, links = result
        # Handle multiple specialties if returned by the pipeline
        if isinstance(result, dict) and "multiple_specialties" in result:
            return AskResponse(
                result=result["message"],
                links=[],
                multiple_specialties=result["multiple_specialties"]
            )

        return AskResponse(result=result, links=links)

    except Exception as e:
        logger.error(f"Error processing /ask request: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# === Multi-turn endpoint ===
@router.post(
    "/chat",
    response_model=ChatResponse,
    tags=["Chatbot"],
    summary="Chat with multi-turn support",
    description="Engage in a back-and-forth conversation with the hospital chatbot. "
                "Uses the conversation service if multi-turn is enabled in config."
                "Please note that this endpoint is still under development and may not fully support multi-turn interactions yet."
)
def chat(request: ChatRequest): # TODO: adjust once multi-turn is fully implemented
    """
    Handles multi-turn conversations. Routes to ConversationService if multi-turn
    is enabled in config, otherwise falls back to single-turn logic.
    """
    try:
        if ENABLE_MULTI_TURN:
            logger.info("Multi-turn chat enabled")
            return conversation_service.handle_chat(request)

        # Fallback: treat as single-turn
        result, links = pipeline.generate_response(prompt=request.prompt,selected_specialty=getattr(request, "selected_specialty", None))
        if isinstance(result, dict) and "multiple_specialties" in result:
            return ChatResponse(
                response=result["message"],
                conversation=[[request.prompt, result["message"]]],
                ambiguous=True,
                multiple_specialties=result["multiple_specialties"]
            )

        return ChatResponse(
            response=result,
            conversation=[[request.prompt, result]],
            ambiguous=False
        )

    except Exception as e:
        logger.error(f"Error processing /chat request: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
