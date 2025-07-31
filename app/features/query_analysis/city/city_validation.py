from app.utility.logging import get_logger
from config.features_config import FOREIGN_CITY_CHECK_EXCEPTION_MSG, AMBIGUOUS_CITY_CHECK_EXCEPTION_MSG

logger = get_logger(__name__)

class CityCheckException(Exception):
    """
    Custom exception for city validation checks.
    """
    pass


class CityChecker:
    """
    Class for city validation and non-French city checks.

    Attributes:
        detector: An instance of a city detection service.      
        llm_handler_service: Optional service for handling LLM interactions.
    Methods:
        validate_french_city(city_status): Validates if a city is French.
        is_city_detection_valid(city_status): Checks if city detection is valid.
        check(user_input, conv_history=""): Checks for non-French cities in user input.
        Raises CityCheckException if a foreign or ambiguous city is detected.
    """
    def __init__(self, detector, llm_handler_service=None):
        logger.info("Initializing CityChecker")
        self.llm_handler_service = llm_handler_service
        self.detector = detector


    def validate_french_city(self, city_status) -> bool:
        """
        Validate if a city is French.
        """
        logger.debug(f"validate_french_city called: city_status={city_status}")
        return self.detector.is_french_city(city_status)


    def is_city_detection_valid(self, city_status) -> bool:
        """
        Check if city detection is valid (not ambiguous or foreign).
        """
        logger.debug(f"is_city_detection_valid called: city_status={city_status}")
        return self.detector.is_valid_city(city_status)


    def check(self, user_input, conv_history=""):
        """
        Checks for non-French cities in user input.
        """
        logger.debug(f"check called: user_input={user_input}, conv_history={conv_history}")
        if not self.detector:
            logger.warning("CityChecker.check: detector is missing, skipping city validation.")
            return  # Skip validation, do not raise exception
        city_result = self.detector.detect_city(user_input, conv_history)
        city_status_type = self.detector.get_city_status_type(city_result)
        if city_status_type == "foreign":
            raise CityCheckException(FOREIGN_CITY_CHECK_EXCEPTION_MSG)
        if city_status_type == "ambiguous":
            raise CityCheckException(AMBIGUOUS_CITY_CHECK_EXCEPTION_MSG)

