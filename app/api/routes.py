"""
Defines all API endpoints for the hospital ranking chatbot.

This file registers the main routes for user queries, health checks, and other
    API functionalities, and organizes them using FastAPI's router system.
"""

from fastapi import APIRouter, Body 
from app.services.pipeline_service import Pipeline
from app.models.query_model import UserQuery
from app.models.response_model import AskResponse
from app.utils.logging import get_logger
logger = get_logger(__name__)

# Initialize the API router instance to define and group related endpoints
router = APIRouter() 
# Initialize the pipeline service to use its methods to process incoming requests
pipeline = Pipeline() 

# Defines a POST endpoint at /ask using the router. 
# This endpoint handles incoming POST requests.
@router.post("/ask", response_model=AskResponse)

def ask_question(query: UserQuery):
    """
    Handles POST requests to the /ask endpoint.
    Processes a user query by passing the prompt and optional specialty to the pipeline,
        and returns the chatbot's response and related links.

    Args:
        query (UserQuery): The user's query containing the prompt and optional specialty.
            Extracted from the request body 
            Expects a JSON object with "prompt" keys.
             CHECK IF SPECIALTY TOO!!!
    Returns:
        dict: JSON object with the chatbot's final answer and links.
    """

    logger.info(f"Received /ask request: {query}")
    # Call pipeline.final_answer and pass the prompt and specialty_st, unpack results
    result, link = pipeline.final_answer(prompt=query.prompt, specialty_st=query.specialty_st)
    logger.info("Response generated for /ask endpoint")
    return {"result": result, "links": link} 
