from app.features.query_analysis.city.city_detection import CityDetector
from app.features.query_analysis.city.city_validation import CityChecker
from app.utility.logging import get_logger

logger = get_logger(__name__)


class CityAnalyst:
    """
    Service to detect, validate, and finalize city results for query_analysis_manager.

    Attributes:
        llm_handler_service: Optional service for handling language model interactions
        model: Optional model for city detection, defaults to None
        detector: Instance of CityDetector for detecting city names
        checker: Instance of CityChecker for validating detected cities
    Methods:
        process_city(prompt: str, conv_history: str = "") -> dict:
            Detects and validates the city from the prompt, returning both city and detection status.
            Raises CityCheckException if the city is foreign or ambiguous.
    """
    def __init__(self, llm_handler_service=None, model=None):
        logger.info("Initializing CityAnalyst")
        self.detector = CityDetector(model)
        self.checker = CityChecker(self.detector, llm_handler_service)

    def process_city(self, prompt: str, conv_history: str = ""):
        logger.debug(f"process_city called: prompt={prompt}, conv_history={conv_history}")
        """
        Detects and validates the city from the prompt, returning both city and detection status, cost, and token_usage.
        """
        # Step 1: Detect city
        city_result = self.detector.detect_city(prompt, conv_history)
        logger.debug(f"CityAnalyst.process_city: city_result={city_result!r}")
        # Step 2: Validate city (side effect, but not used for detection status)
        self.checker.check(prompt, conv_history)
        # Step 3: Finalize and return
        city_value = city_result.get('city') if isinstance(city_result, dict) else city_result
        cost = city_result.get('cost', 0.0) if isinstance(city_result, dict) else 0.0
        detection_method = city_result.get('detection_method', None) if isinstance(city_result, dict) else None
        status_code = city_result.get('status_code', None) if isinstance(city_result, dict) else None
        token_usage = city_result.get('token_usage', {}).get('total_tokens', 0) if isinstance(city_result, dict) else 0.0
        city_detected = bool(city_value and isinstance(city_value, str) and city_value.strip() and city_value.strip().lower() != "aucune correspondance")
        if city_detected:
            logger.info(f"CityAnalyst.process_city: Detected city '{city_value.strip()}', setting city_detected=True")
        else:
            logger.info("CityAnalyst.process_city: No valid city detected, setting city_detected=False")
        return {
            "city": city_value.strip() if city_detected else None,
            "city_detected": city_detected,
            "cost": cost,
            "detection_method": detection_method,
            "status_code": status_code,
            "token_usage": token_usage
        }
