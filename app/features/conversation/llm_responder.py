"""
This module provides a service for managing conversations with an LLM.
"""

from app.utility.wrappers import prompt_formatting
from app.utility.wrappers import parse_llm_response
from app.utility.logging import get_logger
from app.utility.llm_helpers import invoke_llm_with_error_handling

logger = get_logger(__name__) 

class LLMResponder:
    """
    Service for managing conversations with a language model (LLM).
    This service handles conversation continuation, modification detection,
    and query rewriting based on user input and conversation history.
    
    Attributes:
        model: The language model instance used for generating responses.
    """
    def __init__(self, model):
        """
        Initializes the LLMResponder with a language model instance.
        """
        logger.info("Initializing LLMResponder")    
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
        logger.debug(f"continue_conversation called: prompt={prompt}, conv_history={conv_history}")
        formatted_prompt = prompt_formatting(
            "continue_conversation_prompt",
            prompt=prompt,
            conv_history=conv_history
        )
        response_content = invoke_llm_with_error_handling(self.model, formatted_prompt, "continue_conversation")
        logger.debug(f"LLM response: {response_content}")
        return response_content

    def detect_query_modification(self, prompt, conv_history):
        """
        Detects if the user's prompt is a modification of a previous question or a new question.
        Returns numeric code: 0=new_question, 1=modification, 2=ambiguous.
        """
        logger.debug(f"detect_query_modification called: prompt={prompt}, conv_history={conv_history}")
        formatted_prompt = prompt_formatting(
            "detect_modification_prompt",
            prompt=prompt,
            conv_history=conv_history
        )
        raw_response = invoke_llm_with_error_handling(self.model, formatted_prompt, "detect_modification")
        return parse_llm_response(raw_response, "modification")

    def rewrite_query_merge(self, prompt: str, conv_history: str) -> str:
        """
        Rewrite query using merge approach (Case 2).
        
        Args:
            prompt: User's subsequent message
            conv_history: Formatted conversation history
            
        Returns:
            str: The rewritten query with merged filters
        """
        logger.debug(f"rewrite_query_merge called: prompt={prompt}, conv_history={conv_history}")
        formatted_prompt = prompt_formatting(
            "merge_query_rewrite_prompt",
            prompt=prompt,
            conv_history=conv_history
        )
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
        logger.debug(f"rewrite_query_add called: prompt={prompt}, conv_history={conv_history}")
        formatted_prompt = prompt_formatting(
            "add_query_rewrite_prompt",
            prompt=prompt,
            conv_history=conv_history
        )
        return invoke_llm_with_error_handling(self.model, formatted_prompt, "rewrite_query_add")
