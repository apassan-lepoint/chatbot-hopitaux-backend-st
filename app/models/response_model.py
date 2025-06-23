from pydantic import BaseModel
from typing import List

class AskResponse(BaseModel):
    """
    Model for chatbot responses.
    """
    result: str
    links: List[str]