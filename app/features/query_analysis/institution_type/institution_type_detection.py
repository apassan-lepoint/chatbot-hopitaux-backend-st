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
from app.utility.wrappers import prompt_formatting
from app.utility.wrappers import parse_llm_response

logger = get_logger(__name__)

class InstitutionTypeDetector:
    """
    Handles only detection/extraction of institution name and type from prompt using LLM.
    Attributes:
        model: The model used for detection.
        institution_list: A string representing the list of institutions.
    Methods:
        detect_public_private_preference(prompt: str, conv_history: str = "") -> str:
            Detects if the user has a preference for public or private institutions.
            Returns the raw LLM output (e.g., 'public', 'private', 'no match', etc.).
    """
    def __init__(self, model, institution_list: str):
        self.model = model
        self.institution_list = institution_list

    def detect_public_private_preference(self, prompt: str, conv_history: str = "") -> dict:
        """
        Detects if the user has a preference for public or private institutions.
        Returns a dict: {'institution_type': str, 'detection_method': str, 'cost': float, 'token_usage': Any}
        """
        formatted_prompt = prompt_formatting(
            "second_detect_institution_type_prompt",
            prompt=prompt,
            conv_history=conv_history
        )
        llm_response = invoke_llm_with_error_handling(self.model, formatted_prompt, "detect_public_private_preference")
        cost = 0.0
        institution_type = llm_response
        token_usage = 0.0
        if isinstance(llm_response, dict):
            cost = llm_response.get('cost', 0.0)
            institution_type = llm_response.get('content', llm_response)
            token_usage = llm_response.get('token_usage', 0.0)
        parsed_response = parse_llm_response(institution_type, "institution_type")
        logger.debug(f"Public/private preference detection result: {parsed_response}")
        return {'institution_type': parsed_response, 'detection_method': 'llm', 'cost': cost, 'token_usage': token_usage}
        

    

    