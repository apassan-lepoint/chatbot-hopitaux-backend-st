from typing import Optional, Dict
from app.features.query_analysis.institution_name.institution_name_validation import InstitutionNameValidator
from app.features.query_analysis.institution_name.institution_name_detection import InstitutionNameDetector

class InstitutionNameAnalyst:
    """
    Service to detect and validate institution names from a prompt, returning the final result.

    Attributes:
        detector (InstitutionNameDetector): Handles the detection of institution names.
        validator (InstitutionNameValidator): Validates the detected institution names against a list.
    Methods:
        __init__(model, institution_list): Initializes the analyst with a model and an optional institution list.
        set_institution_list(institution_list): Updates the institution list for validation.
        detect_and_validate(prompt, conv_history): Detects and validates the institution name from the prompt
            and conversation history, returning a dictionary with the result.
    """
    def __init__(self, model, institution_list: str = ""):
        self.detector = InstitutionNameDetector(model)
        self.validator = InstitutionNameValidator(institution_list)

    def set_institution_list(self, institution_list: str) -> None:
        """
        Updates the institution list used for validation.
        """
        self.validator.set_institution_list(institution_list)

    def detect_and_validate(self, prompt: str, conv_history: str = "") -> Dict[str, Optional[str]]:
        """
        Detects the institution name from the prompt, validates it, and returns the result dict.
        Only handles institution name logic. Returns a dict with cost, detection_method, and token_usage.
        """
        detected_result = self.detector.detect_specific_institution(
            prompt, self.validator.institution_list, conv_history
        )
        cost = detected_result.get('cost', 0.0) if isinstance(detected_result, dict) else 0.0
        detection_method = detected_result.get('detection_method', None) if isinstance(detected_result, dict) else None
        token_usage = detected_result.get('token_usage', {}).get('total_tokens', 0) if isinstance(detected_result, dict) else 0.0
        detected_name = detected_result.get('institution_name', detected_result) if isinstance(detected_result, dict) else detected_result
        result = self.validator.build_detection_result(detected_name)
        result['cost'] = cost
        result['detection_method'] = detection_method
        result['token_usage'] = token_usage
        return result
