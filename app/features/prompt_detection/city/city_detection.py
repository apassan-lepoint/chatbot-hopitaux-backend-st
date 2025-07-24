"""
Module for detecting cities mentioned in user queries.

This module handles the detection of cities or locations mentioned by users,
including validation for French cities, foreign cities, and ambiguous cases.
It supports conversation history context for better detection accuracy.
"""

from app.utility.logging import get_logger
from app.utility.llm_helpers import invoke_llm_with_error_handling
from app.utility.wrappers import prompt_formatting, parse_llm_response
from app.config.features_config import CITY_MENTIONED, CITY_FOREIGN, CITY_AMBIGUOUS, CITY_NO_CITY_MENTIONED

logger = get_logger(__name__)


class CityDetector:
    """
    Service for detecting cities mentioned in user queries.
    
    This class handles the detection of cities or locations mentioned by users,
    including validation for French cities, foreign cities, and ambiguous cases.
    It supports conversation history context for better detection accuracy.
    """
    
    def __init__(self, model):
        """
        Initialize the CityDetector.
        
        Args:
            model: The language model used for detection
        """
        self.model = model
    
    def _detect_city_status(self, prompt: str, conv_history: str = "") -> int:
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
        formatted_prompt = prompt_formatting("detect_city_prompt", prompt=prompt, conv_history=conv_history)
        raw_response = invoke_llm_with_error_handling(
            self.model, 
            formatted_prompt, 
            "detect_city_status"
        )
        city_status = parse_llm_response(raw_response, "city")
        
        logger.debug(f"City status detection result: {city_status}")
        return city_status
    
    def _detect_city_name(self, prompt: str, conv_history: str = "") -> str:
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
    

    def _get_city_response_description(city_status) -> str:
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
            CITY_NO_CITY_MENTIONED: "No city mentioned",
            CITY_FOREIGN: "Foreign city detected",
            CITY_AMBIGUOUS: "Ambiguous city detection",
            CITY_MENTIONED: "French city mentioned"
        }
        return status_descriptions.get(city_status, f"Unknown status: {city_status}")

    def detect_city(self, prompt: str, conv_history: str = ""):
        """
        Detects the city from the given prompt using the LLM.
        
        This is the main method for city detection. It first determines the status
        of city detection (no city, foreign, ambiguous, or mentioned), and if a
        city is clearly mentioned, it makes a second call to extract the actual
        city name.
        """
        logger.info(f"Detecting city from prompt: '{prompt[:50]}...'")
        
        # First call: detect city status
        city_status = self._detect_city_status(prompt, conv_history)
        
        # If a clear city is mentioned, retrieve the actual city name
        if city_status == CITY_MENTIONED:
            logger.debug("City mentioned detected, extracting city name")
            city_name = self._detect_city_name(prompt, conv_history)
            logger.info(f"City detected: {city_name}")
            return city_name
        logger.info(f"City detection status: {self._get_city_response_description(city_status)}")
        return city_status
    
    
    def get_city_status_type(self, city_status):
        """
        Returns a string representing the type of city status.
        Args:
            city_status: The city detection status or result
        Returns:
            str: One of 'french', 'foreign', 'ambiguous', 'none', or 'unknown'
        """
        if city_status == CITY_MENTIONED or isinstance(city_status, str):
            return "french"
        elif city_status == CITY_FOREIGN:
            return "foreign"
        elif city_status == CITY_AMBIGUOUS:
            return "ambiguous"
        elif city_status == CITY_NO_CITY_MENTIONED:
            return "none"
        else:
            return "unknown"


