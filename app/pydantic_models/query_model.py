"""
query_model.py
---------------------------------
Pydantic models for handling user queries and chat requests in a chatbot application.
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
    user_selected_specialty: str = None  # Optional field for user-selected specialty


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
    user_selected_specialty: str = None  # Optional field for user-selected specialty