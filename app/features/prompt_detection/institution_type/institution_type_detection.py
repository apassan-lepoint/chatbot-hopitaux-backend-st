"""
Module for detecting institution types and names mentioned in user queries.

This module handles the comprehensive detection of institution-related information in user queries,
including:
- Specific hospital/clinic names
- Institution types (Public/Private)
- Type normalization for consistent processing
- Conversation history context support
"""

from app.utility.logging import get_logger
from app.utility.llm_helpers import invoke_llm_with_error_handling
from app.utility.wrappers import prompt_formatting, parse_llm_response

logger = get_logger(__name__)

class InstitutionTypeDetector:
    """
    Handles only detection/extraction of institution name and type from prompt using LLM.
    """
    def __init__(self, model, institution_list: str):
        self.model = model
        self.institution_list = institution_list

    def detect_public_private_preference(self, prompt: str, conv_history: str = "") -> str:
        """
        Detects if the user has a preference for public or private institutions.
        Returns the raw LLM output (e.g., 'public', 'private', 'no match', etc.).
        """
        formatted_prompt = prompt_formatting(
            "second_detect_institution_type_prompt",
            prompt=prompt,
            conv_history=conv_history
        )
        raw_response = invoke_llm_with_error_handling(
            self.model,
            formatted_prompt,
            "detect_public_private_preference"
        )
        parsed_response = parse_llm_response(raw_response, "institution_type")
        logger.debug(f"Public/private preference detection result: {parsed_response}")
        return parsed_response
        

    

    