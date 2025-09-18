""" 
city_validation.py
-------------------
This module defines the CityValidator class, which validates user input for non-French cities.
"""

from app.config.features_config import ERROR_MESSAGES
from app.utility.logging import get_logger


logger = get_logger(__name__)

class CityCheckException(Exception):
    pass


class CityValidator:
    """
    Class to validate user input for non-French cities.
    Attributes:
        llm_handler_service: Service for handling LLM interactions (optional).
        detector: Instance of CityDetector for city detection.
    Methods:
        check(user_input, conv_history=""): Checks for non-French cities in user input.
    """
    def __init__(self, detector, llm_handler_service=None):
        logger.info("Initializing CityValidator")
        self.llm_handler_service = llm_handler_service
        self.detector = detector


    def check(self, user_input, conv_history=""):
        """
        Checks for non-French cities in user input.
        """
        logger.debug(f"check called: user_input={user_input}, conv_history={conv_history}")
        if not self.detector:
            logger.warning("CityValidator.check: detector is missing, skipping city validation.")
            return  # Skip validation, do not raise exception
        city_result = self.detector.detect_city(user_input, conv_history)
        city_status_type = self.detector.get_city_status_type(city_result.get('status_code') if isinstance(city_result, dict) else city_result)
        if city_status_type == "foreign":
            raise CityCheckException(ERROR_MESSAGES["non_french_cities"])
        if city_status_type == "ambiguous":
            raise CityCheckException(ERROR_MESSAGES["ambiguous_city"])
