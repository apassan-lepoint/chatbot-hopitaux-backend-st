"""
Utility functions for common LLM operations.

This module provides helper functions for LLM invocation, response processing,
and error handling that are used across multiple service files.
"""

from app.utility.logging import get_logger

def parse_llm_response(response: str, response_type: str, default=None):
    """
    Unified parser for LLM responses.
    response_type: 'boolean', 'numeric', 'city', 'modification', 'institution_type', 'specialty'
    """
    from app.config.features_config import (
        CITY_NO_CITY_MENTIONED,
        CITY_FOREIGN,
        CITY_AMBIGUOUS,
        CITY_MENTIONED,
        MODIFICATION_NEW_QUESTION,
        MODIFICATION_MODIFICATION,
        MODIFICATION_AMBIGUOUS,
        SPECIALTY_NO_SPECIALTY_MENTIONED,
        SPECIALTY_SINGLE_SPECIALTY,
        SPECIALTY_MULTIPLE_SPECIALTIES
    )
    try:
        resp = response.strip()
        if response_type == "boolean":
            return int(resp) == 1
        if response_type == "numeric":
            return int(resp)
        if response_type == "city":
            code = int(resp)
            valid = {
                CITY_NO_CITY_MENTIONED,
                CITY_FOREIGN,
                CITY_AMBIGUOUS,
                CITY_MENTIONED
            }
            return code if code in valid else CITY_NO_CITY_MENTIONED
        if response_type == "modification":
            code = int(resp)
            valid = {
                MODIFICATION_NEW_QUESTION,
                MODIFICATION_MODIFICATION,
                MODIFICATION_AMBIGUOUS
            }
            return code if code in valid else MODIFICATION_NEW_QUESTION
        if response_type == "institution_type":
            return {0: "no match", 1: "public", 2: "private"}.get(int(resp), "no match")
        if response_type == "specialty":
            return {
                SPECIALTY_NO_SPECIALTY_MENTIONED: "no specialty",
                SPECIALTY_SINGLE_SPECIALTY: "single specialty",
                SPECIALTY_MULTIPLE_SPECIALTIES: "multiple specialties"
            }.get(int(resp), "no specialty")
        # Unknown type, just return stripped response
        return resp
    except (ValueError, AttributeError):
        import logging
        logging.warning(f"Failed to parse {response_type} response: {response}")
        return default

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

