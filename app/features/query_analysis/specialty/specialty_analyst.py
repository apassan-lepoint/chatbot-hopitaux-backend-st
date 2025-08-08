from typing import Optional, Dict, List
from .specialty_detection import SpecialtyDetector
from .specialty_validation import SpecialtyValidator

class SpecialtyAnalyst:
    def __init__(self, model, specialty_list: List[str], specialty_categories_dict):
        self.detector = SpecialtyDetector(model)
        self.validator = SpecialtyValidator(specialty_list, specialty_categories_dict)

    def set_specialty_list(self, specialty_list: List[str]):
        self.validator.specialty_list = specialty_list

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
        raw_specialty, detection_method = self.detector.detect_specialty(prompt, conv_history)
        # Step 2: Normalize specialty
        normalized_specialty = self.validator.normalize_specialty_format(raw_specialty)
        # Step 3: Extract specialty list
        specialty_list = self.validator.extract_specialty_list(normalized_specialty)
        # Step 4: Validate specialty
        is_valid = self.validator.is_specialty_valid(normalized_specialty)
        # Step 5: Calculate confidence
        confidence = self.validator.calculate_confidence(normalized_specialty, detection_method)
        # Step 6: Format for pipeline (string for downstream)
        specialty_str = self._specialty_list_to_string(specialty_list)
        # Step 7: Return all relevant info
        return {
            "specialty": specialty_str,
            "normalized_specialty": normalized_specialty,
            "specialty_list": specialty_list,
            "is_valid": is_valid,
            "confidence": confidence,
            "detection_method": detection_method,
            "raw_specialty": raw_specialty,
            # ...other fields as needed...
        }