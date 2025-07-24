from app.features.prompt_detection.city.city_detection import CityDetector
from app.features.prompt_detection.city.city_validation import CityChecker

class CityService:
    """
    Service to detect, validate, and finalize city results for prompt_detection_manager.
    """
    def __init__(self, llm_handler_service=None, model=None):
        self.detector = CityDetector(model)
        self.checker = CityChecker(self.detector, llm_handler_service)

    def process_city(self, prompt: str, conv_history: str = ""):
        """
        Detects and validates the city from the prompt, returning the final result.
        Args:
            prompt (str): The message to analyze
            conv_history (str, optional): Conversation history for context
        Returns:
            str or int: Final city result (city name or status code)
        Raises:
            CityCheckException: If the city is foreign or ambiguous
        """
        # Step 1: Detect city
        city_result = self.detector.detect_city(prompt, conv_history)
        # Step 2: Validate city
        self.checker.check(prompt, conv_history)
        # Step 3: Finalize and return
        return city_result
