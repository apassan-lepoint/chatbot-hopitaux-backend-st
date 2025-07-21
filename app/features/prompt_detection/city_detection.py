"""
Module for detecting cities mentioned in user queries.

This module handles the detection of cities or locations mentioned by users,
including validation for French cities, foreign cities, and ambiguous cases.
It supports conversation history context for better detection accuracy.
"""

from app.utility.logging import get_logger
from app.utility.llm_helpers import invoke_llm_with_error_handling
from app.utility.wrappers import prompt_formatting, parse_llm_response
from app.config.features_config import CityResponse 

logger = get_logger(__name__)


class CityDetector:
    """
    Service for detecting cities mentioned in user queries.
    
    This class handles the detection of cities or locations mentioned by users,
    including validation for French cities, foreign cities, and ambiguous cases.
    It supports conversation history context for better detection accuracy.
    
    Attributes:
        model: The language model used for detection
        
    Methods:
        detect_city: Main method for detecting cities from user prompts
        detect_city_status: Detects city status (no city, foreign, ambiguous, mentioned)
        detect_city_name: Extracts the actual city name when a city is mentioned
        is_french_city: Validates if a detected city is in France
        is_foreign_city: Checks if a detected city is foreign
        is_ambiguous_city: Checks if city detection is ambiguous
        has_city_mentioned: Checks if any city is mentioned
        get_city_response_description: Gets human-readable description of city response
    """
    
    def __init__(self, model):
        """
        Initialize the CityDetector.
        
        Args:
            model: The language model used for detection
        """
        self.model = model
        
    def detect_city(self, prompt: str, conv_history: str = ""):
        """
        Detects the city from the given prompt using the LLM.
        
        This is the main method for city detection. It first determines the status
        of city detection (no city, foreign, ambiguous, or mentioned), and if a
        city is clearly mentioned, it makes a second call to extract the actual
        city name.
        
        Args:
            prompt (str): The message to analyze
            conv_history (str, optional): Conversation history for context
            
        Returns:
            int or str: 
                - Numeric code for status (0: no city, 1: foreign, 2: ambiguous, 3: mentioned)
                - String with actual city name if specific city found
        """
        logger.info(f"Detecting city from prompt: '{prompt[:50]}...'")
        
        # First call: detect city status
        city_status = self.detect_city_status(prompt, conv_history)
        
        # If a clear city is mentioned, retrieve the actual city name
        if city_status == CityResponse.CITY_MENTIONED:
            logger.debug("City mentioned detected, extracting city name")
            city_name = self.detect_city_name(prompt, conv_history)
            logger.info(f"City detected: {city_name}")
            return city_name
        
        logger.info(f"City detection status: {self.get_city_response_description(city_status)}")
        return city_status
    
    def detect_city_status(self, prompt: str, conv_history: str = "") -> int:
        """
        Detects the city status from the given prompt.
        
        Args:
            prompt (str): The message to analyze
            conv_history (str, optional): Conversation history for context
            
        Returns:
            int: Numeric code for city status
                - 0: no city mentioned
                - 1: foreign city
                - 2: ambiguous city
                - 3: clear city mentioned
        """
        formatted_prompt = prompt_formatting("detect_city_prompt", prompt, conv_history)
        raw_response = invoke_llm_with_error_handling(
            self.model, 
            formatted_prompt, 
            "detect_city_status"
        )
        city_status = parse_llm_response(raw_response, "city")
        
        logger.debug(f"City status detection result: {city_status}")
        return city_status
    
    def detect_city_name(self, prompt: str, conv_history: str = "") -> str:
        """
        Extracts the actual city name from the prompt.
        
        This method should only be called when city status indicates
        that a city is clearly mentioned.
        
        Args:
            prompt (str): The message to analyze
            conv_history (str, optional): Conversation history for context
            
        Returns:
            str: The detected city name
        """
        formatted_prompt = prompt_formatting("second_detect_city_prompt", prompt, conv_history)
        city_name = invoke_llm_with_error_handling(
            self.model, 
            formatted_prompt, 
            "detect_city_name"
        )
        
        logger.debug(f"City name extracted: {city_name}")
        return city_name.strip()
    
    def is_french_city(self, city_status) -> bool:
        """
        Checks if the detected city is a French city.
        
        Args:
            city_status: The city detection status or result
            
        Returns:
            bool: True if it's a French city, False otherwise
        """
        return city_status == CityResponse.CITY_MENTIONED or isinstance(city_status, str)
    
    def is_foreign_city(self, city_status) -> bool:
        """
        Checks if the detected city is a foreign city.
        
        Args:
            city_status: The city detection status
            
        Returns:
            bool: True if it's a foreign city, False otherwise
        """
        return city_status == CityResponse.FOREIGN
    
    def is_ambiguous_city(self, city_status) -> bool:
        """
        Checks if the city detection is ambiguous.
        
        Args:
            city_status: The city detection status
            
        Returns:
            bool: True if city detection is ambiguous, False otherwise
        """
        return city_status == CityResponse.AMBIGUOUS
    
    def has_city_mentioned(self, city_status) -> bool:
        """
        Checks if any city is mentioned in the prompt.
        
        Args:
            city_status: The city detection status
            
        Returns:
            bool: True if any city is mentioned, False otherwise
        """
        return city_status != CityResponse.NO_CITY_MENTIONED
    
    def get_city_response_description(self, city_status) -> str:
        """
        Gets a human-readable description of the city response.
        
        Args:
            city_status: The city detection status
            
        Returns:
            str: Human-readable description of the status
        """
        if isinstance(city_status, str):
            return f"French city: {city_status}"
        
        status_descriptions = {
            CityResponse.NO_CITY_MENTIONED: "No city mentioned",
            CityResponse.FOREIGN: "Foreign city detected",
            CityResponse.AMBIGUOUS: "Ambiguous city detection",
            CityResponse.CITY_MENTIONED: "French city mentioned"
        }
        
        return status_descriptions.get(city_status, f"Unknown status: {city_status}")


# Utility functions for backward compatibility and convenience
def detect_city_from_prompt(model, prompt: str, conv_history: str = ""):
    """
    Utility function for detecting city from prompt.
    
    Args:
        model: The language model to use
        prompt (str): The message to analyze
        conv_history (str, optional): Conversation history for context
        
    Returns:
        int or str: City detection result
    """
    detector = CityDetector(model)
    return detector.detect_city(prompt, conv_history)


def validate_french_city(city_status) -> bool:
    """
    Utility function to validate if a city is French.
    
    Args:
        city_status: The city detection result
        
    Returns:
        bool: True if it's a French city, False otherwise
    """
    detector = CityDetector(None)  # No model needed for validation
    return detector.is_french_city(city_status)


def is_city_detection_valid(city_status) -> bool:
    """
    Utility function to check if city detection is valid (not ambiguous or foreign).
    
    Args:
        city_status: The city detection result
        
    Returns:
        bool: True if detection is valid, False otherwise
    """
    detector = CityDetector(None)  # No model needed for validation
    return detector.is_french_city(city_status)
