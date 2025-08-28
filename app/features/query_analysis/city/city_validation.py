from app.utility.logging import get_logger
from app.config.features_config import WARNING_MESSAGES

logger = get_logger(__name__)

class CityCheckException(Exception):
    """
    Custom exception for city validation checks.
    """
    pass


class CityValidator:
    """
    Class for city validation and non-French city checks.

    Attributes:
        detector: An instance of a city detection service.      
        llm_handler_service: Optional service for handling LLM interactions.
    Methods:
        check(user_input, conv_history=""): Checks for non-French cities in user input.
        Raises CityCheckException if a foreign or ambiguous city is detected.
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
            raise CityCheckException(WARNING_MESSAGES["non_french_cities"])
        if city_status_type == "ambiguous":
            raise CityCheckException(WARNING_MESSAGES["ambiguous_city"])
