class CityCheckException(Exception):
    pass

class CityChecker:
    """
    Class for city validation and non-French city checks.
    """
    def __init__(self, detector, llm_handler_service=None):
        self.llm_handler_service = llm_handler_service
        self.detector = detector

    def validate_french_city(self, city_status) -> bool:
        """
        Validate if a city is French.
        Args:
            city_status: The city detection result
        Returns:
            bool: True if it's a French city, False otherwise
        """
        return self.detector.is_french_city(city_status)

    def is_city_detection_valid(self, city_status) -> bool:
        """
        Check if city detection is valid (not ambiguous or foreign).
        Args:
            city_status: The city detection result
        Returns:
            bool: True if detection is valid, False otherwise
        """
        return self.detector.is_valid_city(city_status)

    def check(self, user_input, conv_history=""):
        """
        Checks for non-French cities in user input.
        Args:
            user_input (str): The user's message
            conv_history (str, optional): Conversation history for context
        Raises:
            CityCheckException: If the city is foreign or ambiguous.
        """
        if not self.llm_handler_service:
            raise CityCheckException("llm_handler_service is required for city checking.")
        city_result = self.llm_handler_service.detect_city(user_input, conv_history)
        if self.detector.is_foreign_city(city_result):
            raise CityCheckException(
                "Je ne peux pas répondre aux questions concernant les hôpitaux situés hors du territoire français, merci de consulter la page du palmarès. [🔗 Page du classement](https://www.lepoint.fr/hopitaux/classements)"
            )
        if self.detector.is_ambiguous_city(city_result):
            raise CityCheckException(
                "Je ne parviens pas à détecter votre localisation, merci de reformuler avec une autre ville."
            )

