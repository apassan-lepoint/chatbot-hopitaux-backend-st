"""
Defines all API endpoints for the hospital ranking chatbot.

This file registers the main routes for user queries, health checks, and other
    API functionalities, and organizes them using FastAPI's router system.
    
## DOUBLE CHECK FUNCTION NAMES UPDATED
"""

from fastapi import APIRouter 
from app.services.pipeline_service import Pipeline
from app.services.llm_service import LLMService
from app.models.query_model import UserQuery, ChatRequest
from app.models.response_model import AskResponse, ChatResponse
from app.utils.formatting import format_links
from app.utils.sanity_checks.fast_api_sanity_checks import (
    check_message_length_fastapi,
    check_conversation_limit_fastapi,
    check_message_pertinence_fastapi,
    check_non_french_cities_fastapi,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Initialize the API router instance to define and group related endpoints
router = APIRouter() 
# Initialize the pipeline service to use its methods to process incoming requests
pipeline = Pipeline() 

# Initialize services once
pipeline = Pipeline()
llm_service = LLMService()

@router.post("/ask", response_model=AskResponse) # Define the /ask endpoint for user queries
def ask_question(query: UserQuery):
    """
    Handles POST requests to the /ask endpoint.
    Processes a user query by passing the prompt and optional specialty to the pipeline,
        and returns the chatbot's response and related links.

    Args:
        query (UserQuery): The user's query containing the prompt and optional specialty.
            Extracted from the request body 
            Expects a JSON object with "prompt" keys.

    Returns:
        dict: JSON object with the chatbot's final answer and links.
    """

    logger.info(f"Received /ask request: {query}")
    
    # Sanity checks for the user query
    check_message_length_fastapi(query.prompt)
    check_message_pertinence_fastapi(query.prompt, llm_service, pertinence_check2=False)
    check_message_pertinence_fastapi(query.prompt, llm_service, pertinence_check2=True)
    check_non_french_cities_fastapi(query.prompt, llm_service)
    
    # Get result
    result, link = pipeline.final_answer(prompt=query.prompt, specialty_st=query.specialty_st)
    logger.info("Response generated for /ask endpoint")
    return {"result": result, "links": link} 

@router.post("/chat", response_model=ChatResponse) # Define the /chat endpoint for multi-turn conversations
def chat(request: ChatRequest):
    """
    Multi-turn chat endpoint. Accepts user prompt and conversation history.
    Determines if the prompt is a modification or a new question.
    
    Args:
        request (ChatRequest): The chat request containing the user's prompt and conversation history.  
    
    Returns:
        ChatResponse: The chatbot's response, updated conversation history, and ambiguity flag.
    """
    
    # Sanity checks for the user query
    check_message_length_fastapi(request.prompt)
    check_message_pertinence_fastapi(request.prompt, llm_service, pertinence_check2=False)
    check_message_pertinence_fastapi(request.prompt, llm_service, pertinence_check2=True)
    check_non_french_cities_fastapi(request.prompt, llm_service)
    check_conversation_limit_fastapi(request.conversation, max_messages=10)    
    
    # Prepare conversation history string for LLM
    conv_history = "\n".join(
        [f"Utilisateur: {q}\nAssistant: {r}" for q, r in request.conversation]
    ) if request.conversation else ""

    mod_type = llm_service.detect_modification(request.prompt, conv_history)
    
    # Handle ambiguous case: return special response for frontend to handle
    if mod_type == "ambiguous":
        return ChatResponse(
            response="Je ne suis pas sûr si votre message est une nouvelle question ou une modification de la précédente. Veuillez préciser.",
            conversation=request.conversation,
            ambiguous=True
        )

    # Handle modification or new question
    if mod_type == "modification":
        result = llm_service.continuer_conv(
            prompt=request.prompt,
            conv_history=request.conversation
        )
        updated_conversation = request.conversation + [[request.prompt, result]]
        return ChatResponse(response=result, conversation=updated_conversation, ambiguous=False)
    
    result, link = pipeline.final_answer(prompt=request.prompt)
    result = format_links(result, link) # Add links to result
    updated_conversation = request.conversation + [[request.prompt, result]]
    return ChatResponse(response=result, conversation=updated_conversation, ambiguous=False)
