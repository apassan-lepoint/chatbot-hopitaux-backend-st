"""
This module provides a service for managing conversations with an LLM.
"""

from app.utils.query_detection.prompt_formatting import (
    format_detect_modification_prompt,
    format_rewrite_query_prompt,
    format_continue_conversation_prompt
)
from app.utils.logging import get_logger

logger = get_logger(__name__) 

class ConversationService:
    def __init__(self, model):
        self.model = model

    def continue_conv_service(self, prompt: str, conv_history: list) -> str:
        formatted_prompt = format_continue_conversation_prompt(prompt, conv_history)
        try:
            response = self.model.invoke(formatted_prompt)
        except Exception as e:
            logger.error(f"LLM invocation failed in continuer_conv: {e}")
            raise
        newanswer = response.content.strip() if hasattr(response, "content") else str(response).strip()
        logger.debug(f"LLM response: {response}")
        return newanswer
    
    def detect_modification_conv_service(self, prompt, conv_history):
        formatted_prompt = format_detect_modification_prompt(prompt, conv_history)
        try:
            response = self.model.invoke(formatted_prompt)
        except Exception as e:
            logger.error(f"LLM invocation failed in detect_modification: {e}")
            raise
        result = response.content.strip().lower() if hasattr(response, "content") else str(response).strip().lower()
        if "modification" in result:
            return "modification"
        if "nouvelle question" in result:
            return "nouvelle question"
        return "ambiguous"

    def rewrite_query_conv_service(self, last_query, modification):
        formatted_prompt = format_rewrite_query_prompt(last_query, modification)
        try:
            response = self.model.invoke(formatted_prompt)
        except Exception as e:
            logger.error(f"LLM invocation failed in rewrite_query: {e}")
            raise
        return response.content.strip() if hasattr(response, "content") else str(response).strip()