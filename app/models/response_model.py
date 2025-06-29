"""
Pydantic models for API responses.

This file defines data validation and serialization models for responses returned
    by the chatbot API, ensuring consistent output structure.
"""

from pydantic import BaseModel
from typing import List

class AskResponse(BaseModel):
    """
    Data model representing the chatbot's response.

    Attributes:
        result (str): The main response or answer from the chatbot.
        links (List[str]): A list of related resource URLs or references.
    """
    result: str
    links: List[str]
    
class ChatResponse(BaseModel):
    """
    Data model for the chat response.

    Attributes:
        response (str): The chatbot's response text.
        conversation (List[List[str]]): The conversation history as a list of message pairs.
        ambiguous (bool): Flag indicating if the response is ambiguous (default is False).
    """
    response: str
    conversation: List[List[str]]
    ambiguous: bool = False