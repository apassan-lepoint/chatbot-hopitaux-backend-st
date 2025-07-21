"""
Utility functions for common LLM operations.

This module provides helper functions for LLM invocation, response processing,
and error handling that are used across multiple service files.
"""

from app.utility.logging import get_logger
from app.utility.wrappers import parse_llm_response

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
        return extract_response_content(response)
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


def log_operation_start(operation_name: str, prompt: str, max_prompt_length: int = 50):
    """
    Standard logging for operation start with truncated prompt.
    
    Args:
        operation_name: Name of the operation
        prompt: User's prompt
        max_prompt_length: Maximum length to show from prompt
    """
    truncated_prompt = prompt[:max_prompt_length] + "..." if len(prompt) > max_prompt_length else prompt
    logger.info(f"{operation_name} for prompt: {truncated_prompt}")


def log_operation_result(operation_name: str, result):
    """
    Standard logging for operation results.
    
    Args:
        operation_name: Name of the operation
        result: The operation result
    """
    logger.debug(f"{operation_name} result: {result}")
