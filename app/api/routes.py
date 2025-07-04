"""
Defines all API endpoints for the hospital ranking chatbot.

This file registers the main routes for user queries, health checks, and other
API functionalities, and organizes them using FastAPI's router system.
"""

from fastapi import APIRouter, HTTPException
from app.services.pipeline_service import Pipeline
from app.services.llm_service import LLMService
from app.models.query_model import UserQuery, ChatRequest
from app.models.response_model import AskResponse, ChatResponse
from app.utils.formatting import format_links
from app.utils.sanity_checks.fast_api_sanity_checks import (
    check_message_length_fastapi,
    check_conversation_limit_fastapi,
    sanity_check_message_pertinence_fastapi,
    check_non_french_cities_fastapi,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Configuration constants
MAX_MESSAGES = 5  # Maximum number of messages allowed in a conversation

# French response messages (could be moved to a constants file for i18n)
AMBIGUOUS_RESPONSE = "Je ne suis pas sûr si votre message est une nouvelle question ou une modification de la précédente. Veuillez préciser."

# Initialize the API router instance to define and group related endpoints
router = APIRouter()

# Initialize services once at module level for performance optimization
# These instances will be reused across all requests to avoid initialization overhead
logger.info("Initializing core services...")
pipeline = Pipeline()
llm_service = LLMService()
logger.info("Core services initialized successfully")

def perform_sanity_checks(prompt: str, conversation: list = None) -> None:
    """
    Perform all sanity checks on user input to ensure request validity.
    
    Args:
        prompt: The user's input message
        conversation: Optional conversation history for chat endpoints
    Raises:
        HTTPException: If any sanity check fails, with appropriate error code and message
        
    Note:
        - pertinent_chatbot_use_case=False: Basic relevance check
        - pertinent_chatbot_use_case=True: Advanced relevance check using different criteria
    """
    logger.debug("Starting sanity checks for user input")
    
    # Check message length to prevent oversized requests
    check_message_length_fastapi(prompt)
    
    # Perform dual-level pertinence checks for content relevance
    sanity_check_message_pertinence_fastapi(prompt, llm_service, pertinent_chatbot_use_case=False)
    sanity_check_message_pertinence_fastapi(prompt, llm_service, pertinent_chatbot_use_case=True)
    
    # Validate geographical scope (French cities only)
    check_non_french_cities_fastapi(prompt, llm_service)
    
    # Check conversation length limits for chat endpoints
    if conversation is not None:
        check_conversation_limit_fastapi(conversation, max_messages=MAX_MESSAGES)
    
    logger.debug("All sanity checks passed successfully")


@router.post("/ask", response_model=AskResponse)
def ask_question(query: UserQuery) -> AskResponse:
    """
    Handles POST requests to the /ask endpoint for single-turn conversations.
    
    Args:
        query: The user's query containing the prompt and optional specialty
    Returns:
        AskResponse: JSON object with the chatbot's final answer and links
    Raises:
        HTTPException: 
            - 400: Bad request (failed sanity checks)
            - 500: Internal server error (processing failures)
    
    Example:
        POST /ask
        {"prompt": "Meilleurs hôpitaux pour cardiologie à Paris", "detected_specialty": "cardiologie"}
    """
    logger.info(f"Received /ask request with prompt length: {len(query.prompt)} chars, specialty: {query.detected_specialty}")
    
    try:
        # Perform comprehensive input validation
        perform_sanity_checks(query.prompt)
        logger.debug("Sanity checks completed for /ask request")
        
        # Process the query through the main pipeline
        logger.debug("Starting pipeline processing for /ask request")
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
    
    Args:
        request: The chat request containing:
                - prompt: Current user message
                - conversation: List of [user_msg, assistant_response] pairs
    
    Returns:
        ChatResponse: Contains:
                     - response: The chatbot's response
                     - conversation: Updated conversation history
                     - ambiguous: Flag indicating if user intent was unclear
    
    Raises:
        HTTPException: 
            - 400: Bad request (failed sanity checks, conversation too long)
            - 500: Internal server error (processing failures)
    """
    logger.info(f"Received /chat request - Prompt length: {len(request.prompt)} chars, "
                f"Conversation history: {len(request.conversation) if request.conversation else 0} turns")
    
    try:
        # Perform comprehensive input validation
        perform_sanity_checks(request.prompt, request.conversation)
        logger.debug("Sanity checks completed for /chat request")
        
        # Prepare conversation history for LLM analysis
        conv_history = "\n".join(
            [f"Utilisateur: {q}\nAssistant: {r}" for q, r in request.conversation]
        ) if request.conversation else ""
        
        # Analyze subsequent message using 4-check system
        logger.debug("Analyzing subsequent message using 4-check system")
        analysis = llm_service.analyze_subsequent_message(request.prompt, conv_history)
        case = llm_service.determine_case(analysis)
        logger.info(f"Determined case: {case}, Analysis: {analysis}")
        
        # Handle different cases
        if case == "case1":
            # Off-topic message
            result = "Je n'ai pas bien saisi la nature de votre demande. Merci de reformuler une question relative aux classements des hôpitaux."
            updated_conversation = request.conversation + [[request.prompt, result]]
            return ChatResponse(response=result, conversation=updated_conversation, ambiguous=False)
        
        elif case == "case2":
            # Continuation + search needed + merge query
            logger.debug("Processing Case 2: merge query and search")
            rewritten_query = llm_service.rewrite_query_merge(request.prompt, conv_history)
            result, links = pipeline.generate_response(prompt=rewritten_query)
            result = format_links(result, links)
            updated_conversation = request.conversation + [[request.prompt, result]]
            return ChatResponse(response=result, conversation=updated_conversation, ambiguous=False)
        
        elif case == "case3":
            # Continuation + search needed + add query
            logger.debug("Processing Case 3: add query and search")
            rewritten_query = llm_service.rewrite_query_add(request.prompt, conv_history)
            result, links = pipeline.generate_response(prompt=rewritten_query)
            result = format_links(result, links)
            updated_conversation = request.conversation + [[request.prompt, result]]
            return ChatResponse(response=result, conversation=updated_conversation, ambiguous=False)
        
        elif case == "case4":
            # Continuation + no search needed (LLM handles)
            logger.debug("Processing Case 4: LLM continuation")
            result = llm_service.continue_conversation(request.prompt, request.conversation)
            updated_conversation = request.conversation + [[request.prompt, result]]
            return ChatResponse(response=result, conversation=updated_conversation, ambiguous=False)
        
        elif case == "case5":
            # New question + search needed
            logger.debug("Processing Case 5: new question with search")
            result, links = pipeline.generate_response(prompt=request.prompt)
            result = format_links(result, links)
            updated_conversation = request.conversation + [[request.prompt, result]]
            return ChatResponse(response=result, conversation=updated_conversation, ambiguous=False)
        
        else:  # case6
            # New question + no search needed (LLM handles)
            logger.debug("Processing Case 6: LLM new question")
            result = llm_service.continue_conversation(request.prompt, request.conversation)
            updated_conversation = request.conversation + [[request.prompt, result]]
            return ChatResponse(response=result, conversation=updated_conversation, ambiguous=False)
        
    except Exception as e:
        logger.error(f"Error processing /chat request: {str(e)}")
        if not isinstance(e, HTTPException):
            raise HTTPException(status_code=500, detail="Internal server error")
        raise
