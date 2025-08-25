"""
Service for orchestrating number_institutions detection and validation.
"""
from .number_institutions_detection import number_institutionsDetector
from .number_institutions_validation import number_institutionsValidation
from app.config.features_config import number_institutions_DEFAULT, number_institutions_MIN, number_institutions_MAX

class NumberInstitutionsAnalyst:
    """
    Service to detect and validate the number of establishments (number_institutions) requested by users.
    It uses a detector to find the number_institutions in the prompt and a validator to ensure it meets the required criteria.

    Attributes:
        detector (number_institutionsDetector): Instance of the detector for number_institutions.
        validator (number_institutionsValidation): Instance of the validator for number_institutions.
        default_number_institutions (int): Default value for number_institutions if none is detected or provided.
        min_number_institutions (int): Minimum allowed value for number_institutions.
        max_number_institutions (int): Maximum allowed value for number_institutions.   
    Methods:
        process_number_institutions(prompt: str, conv_history: str = "", user_number_institutions: int = None) -> int:
            Analyzes the prompt and conversation history to detect and validate the number_institutions value.
            If a user-provided value is given, it will be used; otherwise, the detected value will be validated against the default, minimum, and maximum limits.
            Returns the final validated number_institutions value.      
    """
    def __init__(self, model=None):
        self.detector = number_institutionsDetector(model)
        self.validator = number_institutionsValidation()
        self.default_number_institutions = number_institutions_DEFAULT
        self.min_number_institutions = number_institutions_MIN
        self.max_number_institutions = number_institutions_MAX

    def process_number_institutions(self, prompt: str, conv_history: str = "", user_number_institutions: int = None) -> dict:
        """
        Detects and validates the number_institutions value from the prompt.
        Returns a dict with number_institutions, detection_method, and cost.
        """
        detected_result = self.detector.detect_number_institutions(prompt, conv_history)
        cost = detected_result.get('cost', 0.0) if isinstance(detected_result, dict) else 0.0
        detection_method = detected_result.get('detection_method', None) if isinstance(detected_result, dict) else None
        detected_number_institutions = detected_result.get('number_institutions', detected_result) if isinstance(detected_result, dict) else detected_result
        user_number_institutions = user_number_institutions if user_number_institutions is not None else 0
        final_number_institutions = self.validator.finalize_number_institutions(user_number_institutions, detected_number_institutions, self.default_number_institutions)
        return {
            'number_institutions': final_number_institutions,
            'detection_method': detection_method,
            'cost': cost
        }
