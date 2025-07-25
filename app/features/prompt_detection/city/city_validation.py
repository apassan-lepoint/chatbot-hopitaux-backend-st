from app.utility.logging import get_logger

logger = get_logger(__name__)

class CityCheckException(Exception):
    pass

class CityChecker:
    """
    Class for city validation and non-French city checks.
    """
    def __init__(self, detector, llm_handler_service=None):
        logger.info("Initializing CityChecker")
        self.llm_handler_service = llm_handler_service
        self.detector = detector

    def validate_french_city(self, city_status) -> bool:
        logger.debug(f"validate_french_city called: city_status={city_status}")
        """
        Validate if a city is French.
        Args:
            city_status: The city detection result
        Returns:
            bool: True if it's a French city, False otherwise
        """
        return self.detector.is_french_city(city_status)

    def is_city_detection_valid(self, city_status) -> bool:
        logger.debug(f"is_city_detection_valid called: city_status={city_status}")
        """
        Check if city detection is valid (not ambiguous or foreign).
        Args:
            city_status: The city detection result
        Returns:
            bool: True if detection is valid, False otherwise
        """
        return self.detector.is_valid_city(city_status)

    def check(self, user_input, conv_history=""):
        logger.debug(f"check called: user_input={user_input}, conv_history={conv_history}")
        """
        Checks for non-French cities in user input.
        Args:
            user_input (str): The user's message
            conv_history (str, optional): Conversation history for context
        Raises:
            CityCheckException: If the city is foreign or ambiguous.
        """
        if not self.detector:
            logger.warning("CityChecker.check: detector is missing, skipping city validation.")
            return  # Skip validation, do not raise exception
        city_result = self.detector.detect_city(user_input, conv_history)
        city_status_type = self.detector.get_city_status_type(city_result)
        if city_status_type == "foreign":
            raise CityCheckException(
                "Je ne peux pas répondre aux questions concernant les hôpitaux situés hors du territoire français, merci de consulter la page du palmarès. [🔗 Page du classement](https://www.lepoint.fr/hopitaux/classements)"
            )
        if city_status_type == "ambiguous":
            raise CityCheckException(
                "Je ne parviens pas à détecter votre localisation, merci de reformuler avec une autre ville."
            )

