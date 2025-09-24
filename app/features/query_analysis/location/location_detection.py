"""
location_detection.py
-----------------
This module defines the LocationDetector class, which detects cities mentioned in user queries.
"""

import json
from app.config.features_config import LOCATION_MENTIONED, LOCATION_FOREIGN, LOCATION_AMBIGUOUS, NO_LOCATION_MENTIONED
from app.utility.functions.llm_helpers import invoke_llm_with_error_handling, prompt_formatting
from app.utility.functions.logging import get_logger


logger = get_logger(__name__)

class LocationDetector:
    """
    Class to detect cities mentioned in user queries.
    Attributes:
        model: The language model to use for detection.
    Methods:
        detect_location(prompt, conv_history=""): Detects the location in the given prompt and conversation history.
        get_location_status_type(location_status): Returns a string representing the type of location status.   
    """

    def __init__(self, model):
        logger.info("Initializing LocationDetector")
        self.model = model


    def detect_location(self, prompt: str, conv_history: str = "") -> dict:
        """
        Detect the location mentioned in the user prompt.
        Returns a dict: {'location': dict(region, department, department_number, city_commune, postal_code), 'detection_method': str, 'cost': float, 'status_code': int, 'token_usage': Any}
        """
        # Detect location status
        location_status_formatted_prompt = prompt_formatting("detect_location_prompt", prompt=prompt, conv_history=conv_history)
        location_status_llm_call_result = invoke_llm_with_error_handling(self.model, location_status_formatted_prompt, "detect_location_status")
        location_status_from_llm_call_result = location_status_llm_call_result if isinstance(location_status_llm_call_result, dict) else {"content": location_status_llm_call_result}
        location_status = location_status_from_llm_call_result.get("content")
        logger.debug(f"Location status from LLM detect_location_prompt: {location_status}")
        # Extract cost and token usage from location status detection step
        cost = location_status_from_llm_call_result.get("cost", 0.0)
        token_usage = location_status_from_llm_call_result.get("token_usage", 0.0)

        # Ensure location_status is int for validation
        try:
            location_status_int = int(location_status)
        except (TypeError, ValueError):
            location_status_int = location_status

        valid_location_statuses = [NO_LOCATION_MENTIONED, LOCATION_FOREIGN, LOCATION_AMBIGUOUS, LOCATION_MENTIONED]
        if location_status_int not in valid_location_statuses:
            logger.warning(f"Invalid location status: {location_status}, defaulting to NO_LOCATION_MENTIONED")
            location_status = NO_LOCATION_MENTIONED
        else:
            location_status = location_status_int

        # If location is mentioned, extract/detect the location name
        location_data, detection_method = None, "status"
        if location_status == LOCATION_MENTIONED:
            location_name_formatted_prompt = prompt_formatting("second_detect_location_prompt", prompt=prompt, conv_history=conv_history)
            location_name_llm_call_result = invoke_llm_with_error_handling(self.model, location_name_formatted_prompt, "detect_location_name")
            location_name_from_llm_call_result = location_name_llm_call_result if isinstance(location_name_llm_call_result, dict) else {"content": location_name_llm_call_result}

            raw_location = location_name_from_llm_call_result.get("content")
            logger.debug(f"Raw location from LLM second_detect_location_prompt: {raw_location}")
            
            # Extract cost and token usage from location name detection step
            additional_cost = location_name_from_llm_call_result.get("cost", 0.0)
            additional_tokens = location_name_from_llm_call_result.get("token_usage", 0.0)

            cost += additional_cost
            token_usage = (
                {**token_usage, **additional_tokens}
                if isinstance(token_usage, dict) and isinstance(additional_tokens, dict)
                else additional_tokens or token_usage
            )

            try:
                location_data = json.loads(raw_location) if isinstance(raw_location, str) else raw_location
                detection_method = "llm"
            except Exception:
                logger.warning("Location JSON parsing failed; reverting to LOCATION_NO_LOCATION_MENTIONED")
                location_status = NO_LOCATION_MENTIONED

        logger.debug(f"Location detection result: location={location_data}, status={location_status}, method={detection_method}, cost={cost}, tokens={token_usage}")
        return {'location': location_data, 'detection_method': detection_method, 'cost': cost, 'status_code': location_status, 'token_usage': token_usage}

    def get_location_status_type(self, location_status):
        """
        Returns a string representing the type of location status.
        """
        if isinstance(location_status, str) or location_status == LOCATION_MENTIONED:
            return "french"
        
        return {
            LOCATION_FOREIGN: "foreign",
            LOCATION_AMBIGUOUS: "ambiguous",
            NO_LOCATION_MENTIONED: "none"
        }.get(location_status, "unknown")