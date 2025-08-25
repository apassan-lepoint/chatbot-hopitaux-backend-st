"""
Module for detecting institution names mentioned in user queries.

This module handles the detection of specific hospital/clinic names mentioned by users,
including validation against the institution database and support for conversation
history context for better detection accuracy.
"""

from app.utility.logging import get_logger
from app.utility.llm_helpers import invoke_llm_with_error_handling
from app.utility.wrappers import prompt_formatting


logger = get_logger(__name__)


class InstitutionNameDetector:
    """
    Responsible for extracting institution name or type from prompt using LLM.

    Attributes:
        model: The language model used for detection
        institution_list: Comma-separated list of valid institution names
        conv_history: Conversation history for context      

    Methods:
        detect_specific_institution(prompt: str, institution_list: str, conv_history: str = "")
            Detects if a specific institution is mentioned in the prompt.
            Returns the institution name or "aucune correspondance" if not found.       
    """
    def __init__(self, model):
        self.model = model

    def detect_specific_institution(self, prompt: str, institution_list: str, conv_history: str = "") -> dict:
        """
        Detects if a specific institution is mentioned in the prompt.
        Returns a dict: {'institution_name': str, 'detection_method': str, 'cost': float}
        """
        formatted_prompt = prompt_formatting(
            "detect_institution_type_prompt",
            prompt=prompt,
            institution_list=institution_list,
            conv_history=conv_history
        )
        raw_result = invoke_llm_with_error_handling(
            self.model,
            formatted_prompt,
            "detect_specific_institution"
        )
        cost = 0.0
        institution_name = raw_result
        if isinstance(raw_result, dict):
            cost = raw_result.get('cost', 0.0)
            institution_name = raw_result.get('content', raw_result)
        return {'institution_name': institution_name, 'detection_method': 'llm', 'cost': cost}
        logger.debug(f"Specific institution detection result: {institution_name}")
        return institution_name.strip()


