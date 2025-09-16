"""
Pydantic models for user queries.

This file defines data validation and serialization models for incoming user queries,
    ensuring correct structure and types for API endpoints.
"""

from typing import List
from pydantic import BaseModel

class UserQuery(BaseModel):
    """
    Data model representing a user query to the chatbot.
    
    Attributes:
        prompt (str): The user's input or question for the chatbot.
    """
    prompt: str # Required field for the user's input
    selected_specialty: str = None  # Optional field for user-selected specialty


class ChatRequest(BaseModel):
    """
    Data model for chat requests to the chatbot.
    
    Attributes:
        prompt (str): The user's input or question for the chatbot.
        conversation (List[List[str]]): The conversation history as a list of message pairs,
            where each pair is a list containing the user message and the assistant response.
    """
    prompt: str
    conversation: List[List[str]]  # List of [user, assistant] pairs
    selected_specialty: str = None  # Optional field for user-selected specialty