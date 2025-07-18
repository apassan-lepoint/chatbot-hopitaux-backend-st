
from app.utility.response_parser import CityResponse
from app.features.prompt_detection.city_detection import validate_french_city

class NonFrenchCitiesCheckException(Exception):
    pass

class NonFrenchCitiesChecker:
    def __init__(self, llm_handler_service):
        self.llm_handler_service = llm_handler_service

    def check(self, user_input, conv_history=""):
        """
        Checks for non-French cities in user input.

        Args:
            user_input (str): The user's message
            conv_history (str, optional): Conversation history for context

        Raises:
            NonFrenchCitiesCheckException: If the city is foreign or ambiguous.
        """
        city_result = self.llm_handler_service.detect_city(user_input, conv_history)
        if not validate_french_city(city_result):
            if city_result == CityResponse.FOREIGN:
                raise NonFrenchCitiesCheckException(
                    "Je ne peux pas répondre aux questions concernant les hôpitaux situés hors du territoire français, merci de consulter la page du palmarès. [🔗 Page du classement](https://www.lepoint.fr/hopitaux/classements)"
                )
            if city_result == CityResponse.AMBIGUOUS:
                raise NonFrenchCitiesCheckException(
                    "Je ne parviens pas à détecter votre localisation, merci de reformuler avec une autre ville."
                )
