from app.features.query_analysis.city.city_detection import CityDetector
from app.features.query_analysis.city.city_validation import CityValidator
from app.utility.logging import get_logger

logger = get_logger(__name__)


class CityAnalyst:
    """
    Service to detect, validate, and finalize city results for query_analysis_manager.

    Attributes:
        llm_handler_service: Optional service for handling language model interactions
        model: Optional model for city detection, defaults to None
        detector: Instance of CityDetector for detecting city names
        checker: Instance of CityValidator for validating detected cities
    Methods:
        detect_and_validate_city(prompt: str, conv_history: str = "") -> dict:
            Detects and validates the city from the prompt, returning both city and detection status.
            Raises CityCheckException if the city is foreign or ambiguous.
    """
    def __init__(self, llm_handler_service=None, model=None):
        logger.info("Initializing CityAnalyst")
        self.detector = CityDetector(model)
        self.validator = CityValidator(self.detector, llm_handler_service)

    def detect_and_validate_city(self, prompt: str, conv_history: str = ""):
        """
        Detects and validates the city from the prompt, returning both city and detection status, cost, and token_usage.
        Returns a dict with keys: city, city_detected (bool), cost, detection_method, status_code, token_usage.
        Raises CityCheckException if the city is foreign or ambiguous.
        """
        result = {}

        # Detect and validate city
        logger.info(f"Calling CityDetector.detect_city with prompt: {prompt!r}, conv_history: {conv_history!r}")
        detected_result = self.detector.detect_city(prompt, conv_history)
        logger.info(f"Raw detected_result from CityDetector: {detected_result!r}")
        detected_city_result = (detected_result.get('city') 
                                if isinstance(detected_result, dict) and detected_result.get('city') is not None 
                                else (detected_result.get('content', detected_result) if isinstance(detected_result, dict) else detected_result))
        self.validator.check(prompt, conv_history) # side effect only, not used for detection status
        detected_status_code = detected_result.get('status_code') if isinstance(detected_result, dict) else None
        detected_city_bool = bool(detected_city_result 
                             and isinstance(detected_city_result, str) 
                             and detected_city_result.strip() 
                             and detected_city_result.strip().lower() != "aucune correspondance")
        detected_city = detected_city_result if detected_city_bool else None
        result['status_code'] = detected_status_code
        result['city_detected'] = detected_city_bool
        result['city'] = detected_city

        # Extract detection_method, cost, and token_usage from detection step
        detection_method = detected_result.get('detection_method', None) if isinstance(detected_result, dict) else None
        detected_cost = detected_result.get('cost', 0.0) if isinstance(detected_result, dict) else 0.0
        detected_token_usage = (detected_result.get('token_usage', 0).get('total_tokens', 0)
                                if isinstance(detected_result, dict) and isinstance(detected_result.get('token_usage', 0), dict)
                                else detected_result.get('token_usage', 0) if isinstance(detected_result, dict) else 0.0
                            )
        result['detection_method'] = detection_method
        result['cost'] = detected_cost
        result['token_usage'] = detected_token_usage

        logger.debug(f"City detection and validation result: {result}")

        return result
