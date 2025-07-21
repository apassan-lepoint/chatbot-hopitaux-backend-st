"""
Module for detecting institution types and names mentioned in user queries.

This module handles the comprehensive detection of institution-related information in user queries,
including:
- Specific hospital/clinic names
- Institution types (Public/Private)
- Type normalization for consistent processing
- Conversation history context support
"""

from typing import Optional, Dict, List, Tuple
from app.utility.logging import get_logger
from app.utility.llm_helpers import invoke_llm_with_error_handling
from app.utility.wrappers import prompt_formatting, parse_llm_response

logger = get_logger(__name__)

class InstitutionTypeDetector:
    """
    Comprehensive service for detecting institution types and names in user queries.
    
    This class handles all aspects of institution detection:
    - Specific institution name detection
    - Public/private type detection
    - Type normalization and validation
    - Conversation history context processing
    
    Attributes:
        model: The language model used for detection
        institution_list: List of valid institution names
        institution_mentioned: Boolean flag for institution detection
        institution_name: The detected institution name
        institution_type: The detected institution type
        normalized_type: The normalized institution type
    """
    
    # Type normalization mappings
    TYPE_MAPPING = {
        # No match cases
        "aucune correspondance": "aucune correspondance",
        "no match": "aucune correspondance",
        
        # English variations
        "public": "Public",
        "private": "Privé",
        
        # French variations (ensure consistency)
        "privé": "Privé",
        "prive": "Privé",
        "publique": "Public",
        "privée": "Privé"
    }
    
    # Institution type codes for internal processing
    TYPE_CODES = {
        "no_match": 0,
        "public": 1,
        "private": 2
    }
    
    def __init__(self, model, institution_list: str):
        """
        Initialize the InstitutionTypeDetector.
        
        Args:
            model: The language model used for detection
            institution_list (str): Comma-separated list of valid institution names
        """
        self.model = model
        self.institution_list = institution_list
        self.reset_detection_state()
        
    def detect_institution_type(self, prompt: str, conv_history: str = "") -> str:
        """
        Main method for detecting institution types and names from user queries.
        
        This method orchestrates the entire detection process:
        1. Resets state for new query
        2. Attempts specific institution detection
        3. Falls back to public/private detection if no specific institution found
        4. Normalizes the result for consistent processing
        
        Args:
            prompt (str): The user's message to analyze
            conv_history (str, optional): Conversation history for context
            
        Returns:
            str: The detected and normalized institution type or name
                - Specific institution name if found and valid
                - "Public" for public institutions
                - "Privé" for private institutions
                - "aucune correspondance" if no match found
        """
        logger.info(f"Starting institution type detection for prompt: '{prompt[:50]}...'")
        
        # Reset state for new query
        self.reset_detection_state()
        
        # Step 1: Try to detect specific institution name
        detected_institution = self._detect_specific_institution(prompt, conv_history)
        
        # Step 2: Validate if institution exists in our list
        if self._is_valid_institution(detected_institution):
            self.institution_mentioned = True
            self.institution_name = detected_institution
            logger.info(f"Valid specific institution detected: {detected_institution}")
            return detected_institution
        
        # Step 3: No specific institution found, check for public/private preference
        logger.info("No specific institution found, checking for public/private preference")
        institution_type = self._detect_public_private_preference(prompt, conv_history)
        
        # Step 4: Normalize the type for consistent processing
        normalized_type = self.normalize_institution_type(institution_type)
        self.institution_type = institution_type
        self.normalized_type = normalized_type
        
        logger.info(f"Institution type detection result: {normalized_type}")
        return normalized_type
    
    def _detect_specific_institution(self, prompt: str, conv_history: str = "") -> str:
        """
        Detects if a specific institution name is mentioned in the prompt.
        
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
        
        result = institution_name.strip()
        logger.debug(f"Specific institution detection result: {result}")
        return result
    
    def _detect_public_private_preference(self, prompt: str, conv_history: str = "") -> str:
        """
        Detects if the user has a preference for public or private institutions.
        
        Args:
            prompt (str): The message to analyze
            conv_history (str, optional): Conversation history for context
            
        Returns:
            str: "public", "private", or "no match"
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
        
        # Parse the numeric response (0=no match, 1=public, 2=private)
        parsed_response = parse_llm_response(raw_response, "institution_type")
        
        logger.debug(f"Public/private preference detection result: {parsed_response}")
        return parsed_response
    
    def _is_valid_institution(self, institution_name: str) -> bool:
        """
        Validates if the detected institution name exists in our institution list.
        
        Args:
            institution_name (str): The institution name to validate
            
        Returns:
            bool: True if the institution exists in our list, False otherwise
        """
        if not institution_name or institution_name == "aucune correspondance":
            return False
            
        # Split institution list and check for exact match
        institution_names = [name.strip() for name in self.institution_list.split(",")]
        is_valid = institution_name in institution_names
        
        logger.debug(f"Institution validation: '{institution_name}' -> {is_valid}")
        return is_valid
    
    def normalize_institution_type(self, institution_type: str) -> str:
        """
        Normalizes institution type to consistent format for processing.
        
        This method handles various input formats and converts them to a standardized
        format that can be consistently processed by the rest of the system.
        
        Args:
            institution_type (str): The raw institution type to normalize
            
        Returns:
            str: Normalized institution type
                - "Public" for public institutions
                - "Privé" for private institutions  
                - "aucune correspondance" for no match or invalid input
        """
        if not institution_type or institution_type in ["no match", "aucune correspondance"]:
            return "aucune correspondance"
            
        # Convert to lowercase for comparison
        type_lower = institution_type.lower().strip()
        logger.debug(f"Normalizing institution type: '{institution_type}' -> '{type_lower}'")
        
        # Apply normalization mapping
        normalized = self.TYPE_MAPPING.get(type_lower, "aucune correspondance")
        logger.debug(f"Normalized institution type: '{institution_type}' -> '{normalized}'")
        return normalized
    
    def get_institution_type_code(self, institution_type: str) -> int:
        """
        Converts institution type to numeric code for internal processing.
        
        Args:
            institution_type (str): The institution type to convert
            
        Returns:
            int: Numeric code (0=no match, 1=public, 2=private)
        """
        normalized = self.normalize_institution_type(institution_type)
        
        if normalized == "Public":
            return self.TYPE_CODES["public"]
        elif normalized == "Privé":
            return self.TYPE_CODES["private"]
        else:
            return self.TYPE_CODES["no_match"]
    
    def is_public_institution(self, institution_type: str = None) -> bool:
        """
        Checks if the institution type indicates a public institution.
        
        Args:
            institution_type (str, optional): Type to check, uses current state if not provided
            
        Returns:
            bool: True if public institution, False otherwise
        """
        type_to_check = institution_type or self.normalized_type
        return self.normalize_institution_type(type_to_check) == "Public"
    
    def is_private_institution(self, institution_type: str = None) -> bool:
        """
        Checks if the institution type indicates a private institution.
        
        Args:
            institution_type (str, optional): Type to check, uses current state if not provided
            
        Returns:
            bool: True if private institution, False otherwise
        """
        type_to_check = institution_type or self.normalized_type
        return self.normalize_institution_type(type_to_check) == "Privé"
    
    def has_institution_preference(self) -> bool:
        """
        Checks if the user has expressed any institution preference.
        
        Returns:
            bool: True if user has specific institution or type preference
        """
        return self.institution_mentioned or self.normalized_type != "aucune correspondance"
    
    def get_detection_summary(self) -> Dict:
        """
        Returns a summary of the current detection state.
        
        Returns:
            Dict: Summary containing all detection results
        """
        return {
            "institution_mentioned": self.institution_mentioned,
            "institution_name": self.institution_name,
            "institution_type": self.institution_type,
            "normalized_type": self.normalized_type,
            "has_preference": self.has_institution_preference(),
            "is_public": self.is_public_institution(),
            "is_private": self.is_private_institution()
        }
    
    def set_institution_list(self, institution_list: str):
        """
        Updates the institution list from an external source.
        
        Args:
            institution_list (str): Comma-separated list of valid institution names
        """
        self.institution_list = institution_list
        logger.debug(f"Institution list updated with {len(institution_list.split(','))} institutions")
    
    def reset_detection_state(self):
        """
        Resets the detection state for a new query.
        
        This method should be called before processing a new query to ensure
        clean state and prevent contamination from previous queries.
        """
        self.institution_mentioned = False
        self.institution_name = None
        self.institution_type = None
        self.normalized_type = None
        logger.debug("Institution detection state reset")
    
    # Properties for backward compatibility
    @property
    def institution_mentioned(self) -> bool:
        """Returns whether a specific institution was mentioned."""
        return self._institution_mentioned
    
    @institution_mentioned.setter
    def institution_mentioned(self, value: bool):
        """Sets the institution mentioned flag."""
        self._institution_mentioned = value
    
    @property
    def institution_name(self) -> Optional[str]:
        """Returns the detected institution name."""
        return self._institution_name
    
    @institution_name.setter
    def institution_name(self, value: Optional[str]):
        """Sets the detected institution name."""
        self._institution_name = value
    
    @property
    def institution_type(self) -> Optional[str]:
        """Returns the detected institution type."""
        return self._institution_type
    
    @institution_type.setter
    def institution_type(self, value: Optional[str]):
        """Sets the detected institution type."""
        self._institution_type = value
    
    @property
    def normalized_type(self) -> Optional[str]:
        """Returns the normalized institution type."""
        return self._normalized_type
    
    @normalized_type.setter
    def normalized_type(self, value: Optional[str]):
        """Sets the normalized institution type."""
        self._normalized_type = value




def is_institution_type_valid(institution_type: str) -> bool:
    """
    Checks if an institution type is valid (not "aucune correspondance").
    
    Args:
        institution_type (str): The institution type to validate
        
    Returns:
        bool: True if valid, False if no match
    """
    return institution_type != "aucune correspondance"


def normalize_institution_type_standalone(institution_type: str) -> str:
    """
    Standalone function for normalizing institution types without creating a detector.
    
    Args:
        institution_type (str): The institution type to normalize
        
    Returns:
        str: Normalized institution type
    """
    return InstitutionTypeDetector.TYPE_MAPPING.get(
        institution_type.lower().strip() if institution_type else "",
        "aucune correspondance"
    )