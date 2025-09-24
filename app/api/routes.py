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
from app.services.pipeline_orchestrator_service import PipelineOrchestratorService
from app.utility.functions.logging import get_logger


# Initialize logger for this module
logger = get_logger(__name__)

# Initialize the API router instance to define and group related endpoints
router = APIRouter()

# Services
conversation_service = ConversationService()
pipeline = PipelineOrchestratorService()


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
        result, links = pipeline.generate_response(prompt=query.prompt, user_selected_specialty=getattr(query, "user_selected_specialty", None))
        if isinstance(result, tuple): # Defensive: unpack again if needed
            result, links = result
        # Handle multiple specialties if returned by the pipeline
        if isinstance(result, dict):
            # Accept both keys for backward compatibility, but always send as 'multiple_specialty'
            specialties = result.get("multiple_specialty") or result.get("multiple_specialties")
            logger.debug(f"/ask response debug: result dict={result}, specialties={specialties}, links (should be empty list)={links}")
            if specialties:
                return AskResponse(
                    result=result.get("message", ""),
                    links=[],
                    multiple_specialty=specialties
                )
            # Defensive: if dict but no expected keys, raise error
            logger.error(f"Unexpected dict result from pipeline: {result}")
            raise HTTPException(status_code=500, detail="Internal server error: Unexpected pipeline result format.")
        # Defensive: if result is not a string, raise error
        if not isinstance(result, str):
            logger.error(f"Result is not a string: {result}")
            raise HTTPException(status_code=500, detail="Internal server error: Pipeline result is not a string.")
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
        result, links = pipeline.generate_response(prompt=request.prompt,user_selected_specialty=getattr(request, "user_selected_specialty", None))
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
