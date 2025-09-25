"""
institution_type_detection.py
----------------------------------
Module for detecting institution type (public/private) from user prompts using LLM.
"""

from app.utility.functions.llm_helpers import invoke_llm_with_error_handling
from app.utility.functions.logging import get_logger
from app.utility.functions.llm_helpers import prompt_formatting, parse_llm_response


logger = get_logger(__name__)


class InstitutionTypeDetector:
    """
    Class to detect institution type (public/private) from user prompts using LLM.
    Attributes:
        model: The LLM model to use for detection.  
    Methods:
        detect_institution_type(prompt: str, conv_history: str = "") -> dict:
            Detects if the user has a preference for public or private institutions.
    """
    def __init__(self, model):
        self.model = model

    def detect_institution_type(self, prompt: str, conv_history: str = "") -> dict:
        """
        Detects if the user has a preference for public or private institutions.
        Returns a dict: {'institution_type': str, 'detection_method': str, 'cost': float, 'token_usage': Any}
        """
        formatted_prompt = prompt_formatting("detect_institution_type_prompt", prompt=prompt, conv_history=conv_history)
        llm_call_result = invoke_llm_with_error_handling(self.model, formatted_prompt, "detect_institution_type")
        institution_type_from_llm_call_response = llm_call_result.get('content', llm_call_result) if isinstance(llm_call_result, dict) else llm_call_result
        institution_type = parse_llm_response(institution_type_from_llm_call_response, "institution_type")

        cost = llm_call_result.get('cost', 0.0) if isinstance(llm_call_result, dict) else 0.0
        token_usage = llm_call_result.get('token_usage', 0.0) if isinstance(llm_call_result, dict) else 0.0

        logger.debug(f"Institution type detection result: {institution_type}, {cost}, {token_usage}")
        
        return {'institution_type': institution_type, 'detection_method': 'llm', 'cost': cost, 'token_usage': token_usage}
