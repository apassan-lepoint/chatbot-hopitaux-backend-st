from typing import Optional, Dict, List
from .specialty_detection import SpecialtyDetector
from .specialty_validation import SpecialtyValidator

class SpecialtyAnalyst:
    def __init__(self, model, specialty_list: List[str], specialty_categories_dict):
        self.detector = SpecialtyDetector(model)
        self.validator = SpecialtyValidator(specialty_list, specialty_categories_dict)


    def _specialty_list_to_string(self, validated):
        """Convert a specialty list or string to the expected string format."""
        if isinstance(validated, list):
            if len(validated) == 1:
                return validated[0]
            elif len(validated) > 1:
                return "multiple matches:" + ", ".join(validated)
            else:
                return "no specialty match"
        elif isinstance(validated, str):
            return validated
        else:
            return "no specialty match"

    
    def detect_and_validate_specialty(self, prompt: str, conv_history: str = "") -> Dict[str, Optional[str]]:
        # Step 1: Detect specialty
        detected_specialty, detection_method = self.detector.detect_specialty(prompt, conv_history)
        # Step 2: Validate specialty (returns dict)
        validated_specialty = self.validator.validate_specialty(detected_specialty)
        # Step 3: Format for pipeline (string for downstream)
        detected_validated_specialty = self._specialty_list_to_string(validated_specialty)
        # Step 4: Return all relevant info
        return {
            "specialty": detected_validated_specialty,
            "detection_method": detection_method,
            "original_detected_specialty": detected_specialty
        }
    
    ## Following function kept in case of future need
    # def set_specialty_list(self, specialty_list: List[str]):
    #     self.validator.specialty_list = specialty_list
    