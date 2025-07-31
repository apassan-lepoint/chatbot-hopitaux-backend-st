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

    def detect_specific_institution(self, prompt: str, institution_list: str, conv_history: str = "") -> str:
        """
        Detects if a specific institution is mentioned in the prompt.
        Args:
            prompt (str): The message to analyze
            institution_list (str): Comma-separated list of valid institution names
            conv_history (str, optional): Conversation history for context
        Returns:
            str: The detected institution name or "aucune correspondance"
        """
        formatted_prompt = prompt_formatting(
            "detect_institution_type_prompt",
            prompt=prompt,
            institution_list=institution_list,
            conv_history=conv_history
        )
        institution_name = invoke_llm_with_error_handling(
            self.model,
            formatted_prompt,
            "detect_specific_institution"
        )
        logger.debug(f"Specific institution detection result: {institution_name}")
        return institution_name.strip()


