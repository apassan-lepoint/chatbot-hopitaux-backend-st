from typing import Optional, Dict
from .institution_type_detection import InstitutionTypeDetector
from .institution_type_validation import InstitutionTypeValidator

class InstitutionTypeService:
    """
    Orchestrates detection and validation of institution type only (public/privé/none).
    """
    def __init__(self, model, institution_list: str):
        self.detector = InstitutionTypeDetector(model, institution_list)
        self.validator = InstitutionTypeValidator(institution_list)

    def set_institution_list(self, institution_list: str):
        self.detector.institution_list = institution_list
        self.validator.institution_list = institution_list

    def detect_and_validate_type(self, prompt: str, conv_history: str = "") -> Dict[str, Optional[str]]:
        """
        Detects institution type, validates, and returns a summary dict.
        """
        raw_institution_type = self.detector.detect_public_private_preference(prompt, conv_history)
        institution_type = self.validator.normalize_institution_type(raw_institution_type)
        return {
            "raw_institution_type": raw_institution_type,
            "institution_type": institution_type,
            "is_valid": self.validator.is_institution_type_valid(institution_type)
        }