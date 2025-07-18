"""
Module for detecting institution names mentioned in user queries.

This module handles the detection of specific hospital/clinic names mentioned by users,
including validation against the institution database and support for conversation
history context for better detection accuracy.
"""

from app.utility.logging import get_logger
from app.utility.llm_helpers import invoke_llm_with_error_handling
from app.utility.response_parser import parse_llm_response
from app.utility.wrappers import prompt_formatting


logger = get_logger(__name__)


class InstitutionNameDetector:
    """
    Service for detecting institution names mentioned in user queries.
    
    This class handles the detection of specific hospital/clinic names mentioned by users,
    focusing on the business logic of name detection and type classification.
    Database interactions are handled by the data processing service.
    
    Attributes:
        model: The language model used for detection
        institution_list: List of valid institution names (provided externally)
        institution_mentioned: Boolean flag indicating if institution was mentioned
        institution_name: The detected institution name
        institution_type: The type of the detected institution (Public/Privé)
        
    Methods:
        detect_institution_name: Main method for detecting institution names from user prompts
        detect_specific_institution: Detects if a specific institution is mentioned
        detect_institution_type_fallback: Fallback method to detect public/private preference
        set_institution_list: Sets the institution list from external source
        reset_detection_state: Resets detection state for new queries
    """
    
    def __init__(self, model, institution_list: str = ""):
        """
        Initialize the InstitutionNameDetector.
        
        Args:
            model: The language model used for detection
            institution_list (str): Comma-separated list of valid institution names
        """
        self.model = model
        self.institution_list = institution_list
        self.institution_mentioned = False
        self.institution_name = None
        self.institution_type = None
        
    def detect_institution_name(self, prompt: str, conv_history: str = ""):
        """
        Detects institution names from the given prompt using the LLM.
        Returns a dictionary with institution_name, institution_mentioned, and institution_type.
        """
        logger.info(f"Detecting institution from prompt: '{prompt[:50]}...'")
        institution_name = self.detect_specific_institution(prompt, conv_history)
        institution_names = [name.strip() for name in self.institution_list.split(",")]

        if institution_name in institution_names:
            logger.info(f"Specific institution mentioned: {institution_name}")
            return {
                "institution_name": institution_name,
                "institution_mentioned": True,
                "institution_type": None
            }
        else:
            logger.info("No specific institution detected, checking for public/private preference")
            institution_type = self.detect_institution_type_fallback(prompt, conv_history)
            return {
                "institution_name": None,
                "institution_mentioned": False,
                "institution_type": institution_type
            }
    
    def detect_specific_institution(self, prompt: str, conv_history: str = "") -> str:
        """
        Detects if a specific institution is mentioned in the prompt.
        
        Args:
            prompt (str): The message to analyze
            conv_history (str, optional): Conversation history for context
            
        Returns:
            str: The detected institution name or "aucune correspondance"
        """
        formatted_prompt = prompt_formatting(
            "detect_institution_type_prompt",
            prompt=prompt,
            institution_list=self.institution_list,
            conv_history=conv_history
        )
        
        institution_name = invoke_llm_with_error_handling(
            self.model, 
            formatted_prompt, 
            "detect_specific_institution"
        )
        
        logger.debug(f"Specific institution detection result: {institution_name}")
        return institution_name.strip()
    
    def detect_institution_type_fallback(self, prompt: str, conv_history: str = "") -> str:
        """
        Fallback method to detect public/private institution preference.
        
        This method is called when no specific institution is detected,
        to determine if the user has a preference for public or private institutions.
        
        Args:
            prompt (str): The message to analyze
            conv_history (str, optional): Conversation history for context
            
        Returns:
            str: "Public", "Privé", or "aucune correspondance"
        """
        formatted_prompt = prompt_formatting(
            "second_detect_institution_type_prompt",
            prompt=prompt,
            conv_history=conv_history
        )
        raw_response = invoke_llm_with_error_handling(
            self.model, 
            formatted_prompt, 
            "detect_institution_type_fallback"
        )
        
        institution_type_code = parse_llm_response(raw_response, "institution_type")
        
        # Convert parsed response to expected string format
        if institution_type_code == "public":
            institution_type = "Public"
        elif institution_type_code == "private":
            institution_type = "Privé"
        else:  # "no match"
            institution_type = "aucune correspondance"
            
        logger.debug(f"Institution type fallback result: {institution_type}")
        return institution_type
    
    def set_institution_list(self, institution_list: str):
        """
        Sets the institution list from an external source.
        
        Args:
            institution_list (str): Comma-separated list of valid institution names
        """
        self.institution_list = institution_list
        logger.debug(f"Institution list updated with {len(institution_list.split(','))} institutions")
    
    def reset_detection_state(self):
        """
        Resets the detection state for a new query.
        
        This method should be called before processing a new query to ensure
        clean state.
        """
        self.institution_mentioned = False
        self.institution_name = None
        self.institution_type = None
        logger.debug("Institution detection state reset")
