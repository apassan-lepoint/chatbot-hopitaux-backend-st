from typing import Optional, Dict
from app.features.prompt_detection.institution_name.institution_name_validation import InstitutionNameValidator
from app.features.prompt_detection.institution_name.institution_name_detection import InstitutionNameDetector

class InstitutionNameService:
    """
    Service to detect and validate institution names from a prompt, returning the final result.
    """
    def __init__(self, model, institution_list: str = ""):
        self.detector = InstitutionNameDetector(model)
        self.validator = InstitutionNameValidator(institution_list)

    def set_institution_list(self, institution_list: str) -> None:
        self.validator.set_institution_list(institution_list)

    def detect_and_validate(self, prompt: str, conv_history: str = "") -> Dict[str, Optional[str]]:
        """
        Detects the institution name from the prompt, validates it, and returns the result dict.
        Only handles institution name logic.
        """
        detected_name = self.detector.detect_specific_institution(
            prompt, self.validator.institution_list, conv_history
        )
        return self.validator.build_detection_result(detected_name)
