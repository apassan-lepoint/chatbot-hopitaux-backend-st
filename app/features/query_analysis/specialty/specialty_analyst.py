from typing import Optional, Dict, List
from .specialty_detection import SpecialtyDetector
from .specialty_validation import SpecialtyValidator
from app.utility.logging import get_logger

logger = get_logger(__name__)

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
        """
        Detects the specialty from the prompt, validates it, and returns the result dict.
        Only handles specialty logic. Returns a dict with cost, detection_method, original_detected_specialty, and token_usage.
        """
        result = {}
        
        # Detect and validate specialty
        detected_result = self.detector.detect_specialty(prompt, conv_history)
        detected_specialty = detected_result.get('specialty', detected_result.get('content', detected_result)) if isinstance(detected_result, dict) else detected_result
        validated_specialty = self.validator.validate_specialty(detected_specialty)
        detected_validated_specialty = self._specialty_list_to_string(validated_specialty)
        result['specialty'] = detected_validated_specialty

        # Extract detection_method, cost, and token_usage from detection step
        detection_method = detected_result.get('detection_method', None) if isinstance(detected_result, dict) else None
        detected_cost = detected_result.get('cost', 0.0) if isinstance(detected_result, dict) else 0.0
        detected_token_usage = detected_result.get('total_tokens', 0) if isinstance(detected_result, dict) else 0.0
        result['detection_method'] = detection_method
        result['cost'] = detected_cost
        result['token_usage'] = detected_token_usage
        
        logger.debug(f"Specialty detection and validation result: {result}")
        
        return result
  