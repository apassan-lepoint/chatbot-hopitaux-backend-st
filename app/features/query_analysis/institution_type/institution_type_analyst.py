from typing import Optional, Dict
from .institution_type_detection import InstitutionTypeDetector
from .institution_type_validation import InstitutionTypeValidator

class InstitutionTypeAnalyst:
    """
    Orchestrates detection and validation of institution type only (public/privé/none).
    Uses InstitutionTypeDetector for detection and InstitutionTypeValidator for validation.
    
    Attributes:
        model: The model used for detection.
        institution_list: A string representing the list of institutions.
        detector: An instance of InstitutionTypeDetector.
        validator: An instance of InstitutionTypeValidator. 

    Methods:
        set_institution_list(institution_list: str): Updates the institution list for both detector and validator.
        detect_and_validate_type(prompt: str, conv_history: str = "") -> Dict[str, Optional[str]]:
            Detects the institution type from the prompt and conversation history, validates it,
            and returns a summary dictionary containing the raw institution type, normalized institution type,
            and validation status.  
    """
    def __init__(self, model, institution_list: str):
        self.detector = InstitutionTypeDetector(model, institution_list)
        self.validator = InstitutionTypeValidator(institution_list)

    def set_institution_list(self, institution_list: str):
        """
        Updates the institution list for both detector and validator.
        """
        self.detector.institution_list = institution_list
        self.validator.institution_list = institution_list

    def detect_and_validate_type(self, prompt: str, conv_history: str = "") -> Dict[str, Optional[str]]:
        """
        Detects institution type, validates, and returns a summary dict with cost.
        """
        detected_result = self.detector.detect_public_private_preference(prompt, conv_history)
        cost = 0.0
        raw_institution_type = detected_result
        if isinstance(detected_result, dict):
            cost = detected_result.get('cost', 0.0)
            raw_institution_type = detected_result.get('institution_type', detected_result.get('content', detected_result))
        institution_type = self.validator.normalize_institution_type(raw_institution_type)
        return {
            "raw_institution_type": raw_institution_type,
            "institution_type": institution_type,
            "is_valid": self.validator.is_institution_type_valid(institution_type),
            "cost": cost
        }