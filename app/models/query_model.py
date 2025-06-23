from pydantic import BaseModel

class UserQuery(BaseModel):
    """
    Model for user queries to the chatbot.
    """
    prompt: str
    specialty_st: str | None = None