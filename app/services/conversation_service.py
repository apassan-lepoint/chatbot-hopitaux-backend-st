"""
This module provides a service for managing conversations with an LLM.
"""

from app.utils.query_detection.prompt_formatting import (
    format_detect_modification_prompt,
    format_rewrite_query_prompt,
    format_continue_conversation_prompt,
    format_merge_query_rewrite_prompt,
    format_add_query_rewrite_prompt
)
from app.utils.query_detection.response_parser import parse_modification_response, ModificationResponse
from app.utils.logging import get_logger
from app.utils.llm_helpers import invoke_llm_with_error_handling

logger = get_logger(__name__) 

class ConversationService:
    """
    Service for managing conversations with a language model (LLM).
    This service handles conversation continuation, modification detection,
    and query rewriting based on user input and conversation history.
    
    Attributes:
        model: The language model instance used for generating responses.
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
        response_content = invoke_llm_with_error_handling(self.model, formatted_prompt, "continue_conversation")
        logger.debug(f"LLM response: {response_content}")
        return response_content

    def detect_query_modification(self, prompt, conv_history):
        """
        Detects if the user's prompt is a modification of a previous question or a new question.
        Returns numeric code: 0=new_question, 1=modification, 2=ambiguous.
        """
        formatted_prompt = format_detect_modification_prompt(prompt, conv_history)
        raw_response = invoke_llm_with_error_handling(self.model, formatted_prompt, "detect_modification")
        return parse_modification_response(raw_response)

    def rewrite_modified_query(self, last_query, modification):
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
        return invoke_llm_with_error_handling(self.model, formatted_prompt, "rewrite_query")

    def rewrite_query_merge(self, prompt: str, conv_history: str) -> str:
        """
        Rewrite query using merge approach (Case 2).
        
        Args:
            prompt: User's subsequent message
            conv_history: Formatted conversation history
            
        Returns:
            str: The rewritten query with merged filters
        """
        formatted_prompt = format_merge_query_rewrite_prompt(prompt, conv_history)
        return invoke_llm_with_error_handling(self.model, formatted_prompt, "rewrite_query_merge")

    def rewrite_query_add(self, prompt: str, conv_history: str) -> str:
        """
        Rewrite query using add approach (Case 3).
        
        Args:
            prompt: User's subsequent message
            conv_history: Formatted conversation history
            
        Returns:
            str: The rewritten query with added filters
        """
        formatted_prompt = format_add_query_rewrite_prompt(prompt, conv_history)
        return invoke_llm_with_error_handling(self.model, formatted_prompt, "rewrite_query_add")
