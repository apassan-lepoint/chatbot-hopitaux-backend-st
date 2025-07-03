"""
This module provides a service for managing conversations with an LLM.
"""

from app.utils.query_detection.prompt_formatting import (
    format_detect_modification_prompt,
    format_rewrite_query_prompt,
    format_continue_conversation_prompt
)
from app.utils.response_parser import parse_modification_response, ModificationResponse
from app.utils.logging import get_logger

logger = get_logger(__name__) 

class ConversationService:
    """
    Service for managing conversations with a language model (LLM).
    This service handles conversation continuation, modification detection,
    and query rewriting based on user input and conversation history.
    
    Attributes:
        model: The language model instance used for generating responses.
    
    Methods:
        continue_conversation(prompt: str, conv_history: list) -> str:
            Continues the conversation with the given prompt and history.
        detect_query_modification(prompt: str, conv_history: list) -> str:
            Detects if the prompt is a modification of the previous conversation.
        rewrite_modified_query(last_query: str, modification: str) -> str:
            Rewrites the last query based on the detected modification.
    """
    def __init__(self, model):
        """
        Initializes the ConversationService with a language model instance.
        """
        self.model = model


    def continue_conversation(self, prompt: str, conv_history: list) -> str:
        """
        Continues the conversation with the given prompt and conversation history.

        Args:
            prompt (str): The user's input message to continue the conversation.
            conv_history (list): The conversation history, typically a list of tuples
                                 where each tuple contains a user query and the corresponding response.
        
        Returns:
            str: The model's response to the continued conversation.
        """
        formatted_prompt = format_continue_conversation_prompt(prompt, conv_history)
        
        try:
            response = self.model.invoke(formatted_prompt)
        except Exception as e:
            logger.error(f"LLM invocation failed in continuer_conv: {e}")
            raise
        
        newanswer = response.content.strip() if hasattr(response, "content") else str(response).strip()
        logger.debug(f"LLM response: {response}")
        
        return newanswer
    
    
    def detect_query_modification(self, prompt, conv_history):
        """
        Detects if the user's prompt is a modification of a previous question or a new question.
        Returns numeric code: 0=new_question, 1=modification, 2=ambiguous.
        """
        formatted_prompt = format_detect_modification_prompt(prompt, conv_history)
        
        try:
            response = self.model.invoke(formatted_prompt)
            raw_response = response.content.strip() if hasattr(response, "content") else str(response).strip()
            return parse_modification_response(raw_response)
        except Exception as e:
            logger.error(f"LLM invocation failed in detect_modification: {e}")
            raise


    def rewrite_modified_query(self, last_query, modification): # CHANGE THE NAMES NOT CLEAR 
        """
        Rewrites the last query based on the detected modification.

        Args:
            last_query (str): The last query made by the user.
            modification (str): The detected modification to the last query, typically a clarification or adjustment.
        
        Returns:
            str: The rewritten query based on the modification.
        
        Raises:
            Exception: If the LLM invocation fails.
        """
        formatted_prompt = format_rewrite_query_prompt(last_query, modification)
        
        try:
            response = self.model.invoke(formatted_prompt)
        except Exception as e:
            logger.error(f"LLM invocation failed in rewrite_query: {e}")
            raise
        
        return response.content.strip() if hasattr(response, "content") else str(response).strip()
