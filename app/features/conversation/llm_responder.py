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
    Methods:
        continue_conversation(prompt: str, conv_history: list) -> str:
            Continues the conversation with the LLM based on the user's prompt and conversation history.
        detect_query_modification(prompt: str, conv_history: list) -> int:
            Detects if the user's prompt is a modification of a previous question or a new question.
            Returns numeric code: 0=new_question, 1=modification, 2=ambiguous.
        rewrite_query_merge(prompt: str, conv_history: str) -> str:
            Rewrite query using merge approach (Case 2).
        rewrite_query_add(prompt: str, conv_history: str) -> str:
            Rewrite query using add approach (Case 3).  
    """
    def __init__(self, model):
        logger.info("Initializing LLMResponder")    
        self.model = model


    def continue_conversation(self, prompt: str, conv_history: list) -> dict:
        """
        Continues the conversation with the LLM based on the user's prompt and conversation history.    
        Returns dict with content, cost, token_usage, detection_method.
        """
        logger.debug(f"continue_conversation called: prompt={prompt}, conv_history={conv_history}")
        formatted_prompt = prompt_formatting(
            "continue_conversation_prompt",
            prompt=prompt,
            conv_history=conv_history
        )
        response = invoke_llm_with_error_handling(self.model, formatted_prompt, "continue_conversation")
        logger.debug(f"LLM response: {response}")
        return {
            'content': response.get('content'),
            'cost': response.get('cost', 0.0),
            'token_usage': response.get('token_usage'),
            'detection_method': 'llm'
        }


    def detect_query_modification(self, prompt, conv_history):
        """
        Detects if the user's prompt is a modification of a previous question or a new question.
        Returns dict with result, cost, token_usage, detection_method.
        """
        logger.debug(f"detect_query_modification called: prompt={prompt}, conv_history={conv_history}")
        formatted_prompt = prompt_formatting(
            "detect_modification_prompt",
            prompt=prompt,
            conv_history=conv_history
        )
        response = invoke_llm_with_error_handling(self.model, formatted_prompt, "detect_modification")
        result = parse_llm_response(response.get('content'), "modification")
        return {
            'result': result,
            'cost': response.get('cost', 0.0),
            'token_usage': response.get('token_usage'),
            'detection_method': 'llm'
        }


    def rewrite_query_merge(self, prompt: str, conv_history: str) -> dict:
        """
        Rewrite query using merge approach (Case 2).
        Returns dict with content, cost, token_usage, detection_method.
        """
        logger.debug(f"rewrite_query_merge called: prompt={prompt}, conv_history={conv_history}")
        formatted_prompt = prompt_formatting(
            "merge_query_rewrite_prompt",
            prompt=prompt,
            conv_history=conv_history
        )
        response = invoke_llm_with_error_handling(self.model, formatted_prompt, "rewrite_query_merge")
        return {
            'content': response.get('content'),
            'cost': response.get('cost', 0.0),
            'token_usage': response.get('token_usage'),
            'detection_method': 'llm'
        }


    def rewrite_query_add(self, prompt: str, conv_history: str) -> dict:
        """
        Rewrite query using add approach (Case 3).
        Returns dict with content, cost, token_usage, detection_method.
        """
        logger.debug(f"rewrite_query_add called: prompt={prompt}, conv_history={conv_history}")
        formatted_prompt = prompt_formatting(
            "add_query_rewrite_prompt",
            prompt=prompt,
            conv_history=conv_history
        )
        response = invoke_llm_with_error_handling(self.model, formatted_prompt, "rewrite_query_add")
        return {
            'content': response.get('content'),
            'cost': response.get('cost', 0.0),
            'token_usage': response.get('token_usage'),
            'detection_method': 'llm'
        }
