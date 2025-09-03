"""
This file registers the main routes for user queries, health checks, and other
API functionalities, and organizes them using FastAPI's router system.
"""

from fastapi import APIRouter, HTTPException

from app.services.pipeline_orchestrator_service import PipelineOrchestrator
from app.services.llm_handler_service import LLMHandler
from app.pydantic_models.query_model import UserQuery, ChatRequest
from app.pydantic_models.response_model import AskResponse, ChatResponse
from app.utility.formatting_helpers import format_links
from app.features.conversation.conversation_analyst import ConversationAnalyst
from app.utility.logging import get_logger
from app.config.features_config import WARNING_MESSAGES, INTERNAL_SERVER_ERROR_MSG
from app.services.conversation_service import ConversationService
from app.config.features_config import ENABLE_MULTI_TURN

# Initialize logger for this module
logger = get_logger(__name__)


# Initialize the API router instance to define and group related endpoints
router = APIRouter()

# Services
conversation_service = ConversationService()
pipeline = PipelineOrchestrator()


# === Single-turn endpoint ===
@router.post("/ask", response_model=AskResponse)
def ask_question(query: UserQuery):
    """
    Handles single-turn queries using the pipeline only.
    """
    try:
        result, links = pipeline.generate_response(prompt=query.prompt, selected_specialty=getattr(query, "selected_specialty", None))

        # Handle multiple specialties if returned by the pipeline
        if isinstance(result, dict) and "multiple_specialties" in result:
            return AskResponse(
                result=result["message"],
                links=[],
                ambiguous=True,
                multiple_specialties=result["multiple_specialties"]
            )

        return AskResponse(result=result, links=links)

    except Exception as e:
        logger.error(f"Error processing /ask request: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# === Multi-turn endpoint ===
@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
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
