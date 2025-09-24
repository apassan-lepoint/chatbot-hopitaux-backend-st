""" 
number_institutions_analyst.py
-------------------------
This module defines the NumberInstitutionsAnalyst class, which detects and validates
the number of establishments (number_institutions) requested by users in their prompts.
"""

from app.config.features_config import number_institutions_DEFAULT, number_institutions_MIN, number_institutions_MAX
from .number_institutions_detection import number_institutionsDetector
from .number_institutions_validation import NumberInstitutionsValidator
from app.utility.functions.logging import get_logger


logger = get_logger(__name__)


class NumberInstitutionsAnalyst:
    """
    Class to detect and validate the number of establishments (number_institutions) from user prompts.
    Attributes:
        detector (number_institutionsDetector): Detector for extracting number_institutions from prompts.
        validator (NumberInstitutionsValidator): Validator for ensuring number_institutions is within acceptable bounds.
        default_number_institutions (int): Default number of institutions to use if none is specified.
        min_number_institutions (int): Minimum allowable number of institutions.
        max_number_institutions (int): Maximum allowable number of institutions.
    Methods:
        process_number_institutions(prompt, conv_history="", user_number_institutions=None):
            Detects and validates the number_institutions value from the prompt.
            Returns a dict with number_institutions, detection_method, cost, and token_usage.      
    """
    def __init__(self, model=None):
        self.detector = number_institutionsDetector(model)
        self.validator = NumberInstitutionsValidator()
        self.default_number_institutions = number_institutions_DEFAULT
        self.min_number_institutions = number_institutions_MIN
        self.max_number_institutions = number_institutions_MAX

    def process_number_institutions(self, prompt: str, conv_history: str = "", user_number_institutions: int = None) -> dict:
        """
        Detects and validates the number_institutions value from the prompt.
        Returns a dict with number_institutions, detection_method, cost, and token_usage.
        """
        result = {}

        # Detect and validate number_institutions
        detected_result = self.detector.detect_number_institutions(prompt, conv_history)
        detected_number_institutions = detected_result.get('number_institutions', detected_result) if isinstance(detected_result, dict) else detected_result
        user_number_institutions = user_number_institutions if user_number_institutions is not None else 0
        detected_validated_number_institutions = self.validator.finalize_number_institutions(user_number_institutions, detected_number_institutions, self.default_number_institutions)
        result['number_institutions'] = detected_validated_number_institutions

        # Extract detection_method, cost, and token_usage from detection step
        detection_method = detected_result.get('detection_method', None) if isinstance(detected_result, dict) else None
        detected_cost = detected_result.get('cost', 0.0) if isinstance(detected_result, dict) else 0.0
        detected_token_usage = detected_result.get('token_usage', {}).get('total_tokens', 0) if isinstance(detected_result, dict) else 0.0
        result['detection_method'] = detection_method
        result['cost'] = detected_cost
        result['token_usage'] = detected_token_usage
        
        logger.debug(f"Number of institutions detection and validation result: {result}")

        return result
