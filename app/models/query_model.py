"""
Pydantic models for user queries.

This file defines data validation and serialization models for incoming user queries,
    ensuring correct structure and types for API endpoints.
"""

from pydantic import BaseModel

class UserQuery(BaseModel):
    """
    Data model representing a user query to the chatbot.

    Attributes:
        prompt (str): The user's input or question for the chatbot.
        specialty_st (str | None): Optional medical specialty context for the query.
    """
    prompt: str # Required field for the user's input
    specialty_st: str | None = None # Optional field for medical specialty
    