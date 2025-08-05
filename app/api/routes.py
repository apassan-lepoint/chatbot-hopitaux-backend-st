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
from app.features.sanity_checks.sanity_checks_analyst import SanityChecksAnalyst
from app.features.conversation.conversation_analyst import ConversationAnalyst
from app.utility.logging import get_logger
from app.config.features_config import (MAX_MESSAGES, CHECKS_TO_RUN_Q1, CHECKS_TO_RUN_MULTI_TURN, OFF_TOPIC_RESPONSE, INTERNAL_SERVER_ERROR_MSG)

# Initialize logger for this module
logger = get_logger(__name__)

# Initialize the API router instance to define and group related endpoints
router = APIRouter()

# Initialize services once at module level for performance optimization
logger.info("Initializing core services...")
pipeline = PipelineOrchestrator()
llm_handler_service = LLMHandler()
conv_manager = ConversationAnalyst(llm_handler_service.model)
logger.info("Core services initialized successfully")

def perform_sanity_checks(prompt: str, conversation: list = None, checks_to_run=None) -> None:
    """
    Perform selected sanity checks on user input to ensure request validity.
    """
    logger.debug("Starting sanity checks for user input")
    conv_history = ""
    if conversation is not None and len(conversation) > 0:
        conv_history = "\n".join([f"Utilisateur: {q}\nAssistant: {r}" for q, r in conversation])
        logger.debug("Checking pertinence with full conversation context")
    else:
        logger.debug("Checking pertinence without conversation context")

    sanity_checks_manager = SanityChecksAnalyst(llm_handler_service, max_messages=MAX_MESSAGES)
    results = sanity_checks_manager.run_checks(prompt, conversation, conv_history, checks_to_run=checks_to_run)
    for check, result in results.items():
        if not result["passed"]:
            raise HTTPException(status_code=400, detail=result["error"])
    logger.debug("All sanity checks passed successfully")


@router.post("/ask", response_model=AskResponse)
def ask_question(query: UserQuery) -> AskResponse:
    """
    Handles POST requests to the /ask endpoint for single-turn conversations.
    Validates the user query, performs sanity checks, and generates a response
    using the pipeline orchestrator.  
    """
    logger.info(f"Received /ask request with prompt length: {len(query.prompt)} chars, specialty: {query.detected_specialty}")
    try:
        perform_sanity_checks(query.prompt, checks_to_run=CHECKS_TO_RUN_Q1)
        logger.debug("Sanity checks completed for /ask request")
        # For consistency, pass conv_history (empty for single-turn) to pipeline
        result, links = pipeline.generate_response(prompt=query.prompt, detected_specialty=query.detected_specialty)
        logger.info(f"Response generated for /ask endpoint - Links found: {len(links) if links else 0}")
        return AskResponse(result=result, links=links)
    except Exception as e:
        logger.error(f"Error processing /ask request - Prompt: '{query.prompt[:100]}...', Error: {str(e)}")
        if not isinstance(e, HTTPException):
            raise HTTPException(status_code=500, detail="Internal server error")
        raise


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """
    Multi-turn chat endpoint using 6-case approach.
    Determines how to handle the user's subsequent message based on 4 checks:
    1. Is it on-topic?
    2. Is it a continuation of conversation?
    3. Does it need search in hospital data?
    4. How should queries be merged?
    
    Returns:
        ChatResponse: Contains:
        - response: The chatbot's response
        - conversation: Updated conversation history
        - ambiguous: Flag indicating if user intent was unclear
    """
    logger.info(f"Received /chat request - Prompt length: {len(request.prompt)} chars, "
                f"Conversation history: {len(request.conversation) if request.conversation else 0} turns")
    try:
        perform_sanity_checks(request.prompt, request.conversation, checks_to_run=CHECKS_TO_RUN_MULTI_TURN)
        logger.debug("Sanity checks completed for /chat request")
        conv_history = request.conversation if request.conversation else []
        # Use ConversationAnalyst for consolidated conversation logic
        conv_results = conv_manager.run_all_conversation_checks(request.prompt, conv_history)
        multi_turn_result = conv_results["multi_turn_result"]
        # Determine case from multi_turn_result
        case = multi_turn_result.get("case") if isinstance(multi_turn_result, dict) else None
        # Fallback to previous logic if case is not set
        if not case:
            conv_history_str = "\n".join([f"Utilisateur: {q}\nAssistant: {r}" for q, r in conv_history])
            analysis = llm_handler_service.analyze_subsequent_message(request.prompt, conv_history_str)
            case = llm_handler_service.determine_case(analysis)
        logger.info(f"Determined case: {case}, Analysis: {multi_turn_result}")
        if case == "case1":
            result = OFF_TOPIC_RESPONSE
            updated_conversation = conv_history + [[request.prompt, result]]
            return ChatResponse(response=result, conversation=updated_conversation, ambiguous=False)
        elif case == "case2":
            logger.debug("Processing Case 2: merge query and search")
            conv_history_str = "\n".join([f"Utilisateur: {q}\nAssistant: {r}" for q, r in conv_history])
            rewritten_query = llm_handler_service.rewrite_query_merge(request.prompt, conv_history_str)
            result, links = pipeline.generate_response(prompt=rewritten_query)
            result = format_links(result, links)
            updated_conversation = conv_history + [[request.prompt, result]]
            return ChatResponse(response=result, conversation=updated_conversation, ambiguous=False)
        elif case == "case3":
            logger.debug("Processing Case 3: add query and search")
            conv_history_str = "\n".join([f"Utilisateur: {q}\nAssistant: {r}" for q, r in conv_history])
            rewritten_query = llm_handler_service.rewrite_query_add(request.prompt, conv_history_str)
            result, links = pipeline.generate_response(prompt=rewritten_query)
            result = format_links(result, links)
            updated_conversation = conv_history + [[request.prompt, result]]
            return ChatResponse(response=result, conversation=updated_conversation, ambiguous=False)
        elif case == "case4":
            logger.debug("Processing Case 4: LLM continuation")
            result = conv_results["continued_response"]
            updated_conversation = conv_history + [[request.prompt, result]]
            return ChatResponse(response=result, conversation=updated_conversation, ambiguous=False)
        elif case == "case5":
            logger.debug("Processing Case 5: new question with search")
            result, links = pipeline.generate_response(prompt=request.prompt)
            result = format_links(result, links)
            updated_conversation = conv_history + [[request.prompt, result]]
            return ChatResponse(response=result, conversation=updated_conversation, ambiguous=False)
        else:  # case6
            logger.debug("Processing Case 6: LLM new question")
            result = conv_results["continued_response"]
            updated_conversation = conv_history + [[request.prompt, result]]
            return ChatResponse(response=result, conversation=updated_conversation, ambiguous=False)
    except Exception as e:
        logger.error(f"Error processing /chat request: {str(e)}")
        if not isinstance(e, HTTPException):
            raise HTTPException(status_code=500, detail=INTERNAL_SERVER_ERROR_MSG)
        raise
