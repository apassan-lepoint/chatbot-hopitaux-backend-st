"""
city_detection.py
-----------------
This module defines the CityDetector class, which detects cities mentioned in user queries.
"""

from app.config.features_config import CITY_MENTIONED, CITY_FOREIGN, CITY_AMBIGUOUS, CITY_NO_CITY_MENTIONED
from app.utility.llm_helpers import invoke_llm_with_error_handling
from app.utility.logging import get_logger
from app.utility.wrappers import prompt_formatting


logger = get_logger(__name__)

class CityDetector:
    """
    Class to detect cities mentioned in user queries.
    Attributes:
        model: The language model to use for detection.
    Methods:
        detect_city(prompt, conv_history=""): Detects the city in the given prompt and conversation history.
        get_city_status_type(city_status): Returns a string representing the type of city status.   
    """

    def __init__(self, model):
        logger.info("Initializing CityDetector")
        self.model = model


    def detect_city(self, prompt: str, conv_history: str = "") -> dict:
        """
        Detect the city mentioned in the user prompt.
        Returns a dict: {'city': str, 'detection_method': str, 'cost': float, 'status_code': int, 'token_usage': Any}
        """
        # Detect city status
        city_status_formatted_prompt = prompt_formatting("detect_city_prompt", prompt=prompt, conv_history=conv_history)
        city_status_llm_call_result = invoke_llm_with_error_handling(self.model, city_status_formatted_prompt, "detect_city_status")
        city_status_from_llm_call_result = city_status_llm_call_result if isinstance(city_status_llm_call_result, dict) else {"content": city_status_llm_call_result}
        city_status = city_status_from_llm_call_result.get("content")

        # Extract cost and token usage from city status detection step
        cost = city_status_from_llm_call_result.get("cost", 0.0)
        token_usage = city_status_from_llm_call_result.get("token_usage", 0.0)

        # Ensure city_status is int for validation
        try:
            city_status_int = int(city_status)
        except (TypeError, ValueError):
            city_status_int = city_status

        valid_city_statuses = [CITY_NO_CITY_MENTIONED, CITY_FOREIGN, CITY_AMBIGUOUS, CITY_MENTIONED]
        if city_status_int not in valid_city_statuses:
            logger.warning(f"Invalid city status: {city_status}, defaulting to CITY_NO_CITY_MENTIONED")
            city_status = CITY_NO_CITY_MENTIONED
        else:
            city_status = city_status_int

        # If city is mentioned, extract/detect the city name
        city_name, detection_method = None, "status"
        if city_status == CITY_MENTIONED:
            city_name_formatted_prompt = prompt_formatting("second_detect_city_prompt", prompt=prompt, conv_history=conv_history)
            city_name_llm_call_result = invoke_llm_with_error_handling(self.model, city_name_formatted_prompt, "detect_city_name")
            city_name_from_llm_call_result = city_name_llm_call_result if isinstance(city_name_llm_call_result, dict) else {"content": city_name_llm_call_result}

            raw_city = city_name_from_llm_call_result.get("content")
            additional_cost = city_name_from_llm_call_result.get("cost", 0.0)
            additional_tokens = city_name_from_llm_call_result.get("token_usage", 0.0)

            cost += additional_cost
            token_usage = (
                {**token_usage, **additional_tokens}
                if isinstance(token_usage, dict) and isinstance(additional_tokens, dict)
                else additional_tokens or token_usage
            )

            if isinstance(raw_city, str) and raw_city.strip():
                city_name = raw_city.strip()
                detection_method = "llm"
            else:
                logger.warning("City name extraction failed; reverting to CITY_NO_CITY_MENTIONED")
                city_status = CITY_NO_CITY_MENTIONED

        logger.debug(f"City detection result: city={city_name}, status={city_status}, method={detection_method}, cost={cost}, tokens={token_usage}")
        return {'city': city_name, 'detection_method': detection_method, 'cost': cost, 'status_code': city_status, 'token_usage': token_usage}

    def get_city_status_type(self, city_status):
        """
        Returns a string representing the type of city status.
        """
        if isinstance(city_status, str) or city_status == CITY_MENTIONED:
            return "french"
        
        return {
            CITY_FOREIGN: "foreign",
            CITY_AMBIGUOUS: "ambiguous",
            CITY_NO_CITY_MENTIONED: "none"
        }.get(city_status, "unknown")