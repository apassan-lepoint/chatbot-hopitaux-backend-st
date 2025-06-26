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