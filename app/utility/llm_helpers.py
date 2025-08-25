"""
Utility functions for common LLM operations.

This module provides helper functions for LLM invocation, response processing,
and error handling that are used across multiple service files.
"""


from app.utility.logging import get_logger
from app.utility.wrappers import parse_llm_response
from app.config.features_config import TRACK_LLM_CALL_COST, INPUT_PROMPT_PRICE_PER_TOKEN, OUTPUT_COMPLETION_PRICE_PER_TOKEN


logger = get_logger(__name__)


def extract_response_content(response) -> str:
    """
    Extract content from LLM response object, handling different response types.
    
    Args:
        response: LLM response object
        
    Returns:
        str: Extracted and stripped response content
    """
    return response.content.strip() if hasattr(response, "content") else str(response).strip()


def invoke_llm_with_error_handling(model, formatted_prompt, operation_name: str):
    """
    Generic function to invoke LLM with consistent error handling and logging.
    
    Args:
        model: The LLM model instance
        formatted_prompt: The formatted prompt to send to the LLM
        operation_name: Name of the operation for error logging
        
    Returns:
        The extracted response content
        
    Raises:
        Exception: If the LLM invocation fails
    """
    try:
        response = model.invoke(formatted_prompt)
        content = extract_response_content(response)
        token_usage = None
        cost = None
        if TRACK_LLM_CALL_COST:
            # OpenAI/LLM responses often have a 'usage' or 'token_usage' attribute
            if hasattr(response, 'usage'):
                usage = response.usage
                prompt_tokens = usage.get('prompt_tokens') if isinstance(usage, dict) else getattr(usage, 'prompt_tokens', None)
                completion_tokens = usage.get('completion_tokens') if isinstance(usage, dict) else getattr(usage, 'completion_tokens', None)
                total_tokens = usage.get('total_tokens') if isinstance(usage, dict) else getattr(usage, 'total_tokens', None)
                token_usage = {
                    'prompt_tokens': prompt_tokens,
                    'completion_tokens': completion_tokens,
                    'total_tokens': total_tokens
                }
            if hasattr(response, 'cost'):
                cost = response.cost
            # Calculate cost using input/output prices
            if token_usage:
                cost = 0.0
                if token_usage['prompt_tokens']:
                    cost += token_usage['prompt_tokens'] * INPUT_PROMPT_PRICE_PER_TOKEN
                if token_usage['completion_tokens']:
                    cost += token_usage['completion_tokens'] * OUTPUT_COMPLETION_PRICE_PER_TOKEN
        return {
            'content': content,
            'token_usage': token_usage if TRACK_LLM_CALL_COST else None,
            'cost': cost if TRACK_LLM_CALL_COST else None
        }
    except Exception as e:
        logger.error(f"LLM invocation failed in {operation_name}: {e}")
        raise


def invoke_llm_and_parse_boolean(model, formatted_prompt, operation_name: str) -> bool:
    """
    Generic function to invoke LLM and parse boolean response.
    
    Args:
        model: The LLM model instance
        formatted_prompt: The formatted prompt to send to the LLM
        operation_name: Name of the operation for error logging
        
    Returns:
        bool: Parsed boolean response
        
    Raises:
        Exception: If the LLM invocation fails
    """
    try:
        response = model.invoke(formatted_prompt)
        raw_response = extract_response_content(response)
        return parse_llm_response(raw_response, "boolean")
    except Exception as e:
        logger.error(f"LLM invocation failed in {operation_name}: {e}")
        raise

