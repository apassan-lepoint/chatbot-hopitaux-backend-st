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
        Detects and validates the city from the prompt, returning both city and detection status.
        """
        # Step 1: Detect city
        city_result = self.detector.detect_city(prompt, conv_history)
        logger.debug(f"CityAnalyst.process_city: city_result={city_result!r}")
        # Step 2: Validate city (side effect, but not used for detection status)
        self.checker.check(prompt, conv_history)
        # Step 3: Finalize and return
        from app.config.features_config import CITY_MENTIONED
        if isinstance(city_result, str) and city_result.strip() and city_result.strip().lower() != "aucune correspondance":
            logger.info(f"CityAnalyst.process_city: Detected city '{city_result.strip()}', setting city_detected=True")
            return {"city": city_result.strip(), "city_detected": True}
        else:
            logger.info("CityAnalyst.process_city: No valid city detected, setting city_detected=False")
            return {"city": None, "city_detected": False}
