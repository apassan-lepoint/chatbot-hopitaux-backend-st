from typing import Optional, Dict
from app.features.query_analysis.institution_names.institution_names_validation import InstitutionNamesValidator
from app.features.query_analysis.institution_names.institution_names_detection import InstitutionNamesDetector
from app.utility.logging import get_logger

logger = get_logger(__name__)

class InstitutionNamesAnalyst:
    """
    Service to detect and validate institution names from a prompt, returning the final result.

    Attributes:
        detector (InstitutionNamesDetector): Handles the detection of institution names.
        validator (InstitutionNamesValidator): Validates the detected institution names against a list.
    Methods:
        __init__(model, institution_list): Initializes the analyst with a model and an optional institution list.
        set_institution_list(institution_list): Updates the institution list for validation.
        detect_and_validate_instution_name(prompt, conv_history): Detects and validates the institution name from the prompt
            and conversation history, returning a dictionary with the result.
    """
    def __init__(self, model=None):
        self.detector = InstitutionNamesDetector(model)
        self.validator = InstitutionNamesValidator()

    # def set_institution_list(self, institution_list: str) -> None:
    #     """
    #     Updates the institution list used for validation.
    #     """
    #     self.validator.set_institution_list(institution_list)
    #     logger.debug(f"Institution list updated with {len(self.institution_list)} institutions")

    # def detect_and_validate_institution_names(self, prompt: str, conv_history: str = "") -> Dict[str, Optional[str]]:
    #     """
    #     Detects the institution name from the prompt, validates it, and returns the result dict.
    #     """
    #     # Detect and validate institution name
    #     detected_result = self.detector.detect_institution_names(prompt, self.validator.institution_list, conv_history)
    #     detected_institution_names = detected_result.get('institution_names', detected_result) if isinstance(detected_result, dict) else detected_result
    #     result = self.validator.build_detection_result(detected_institution_names)
        
    #     # Extract detection_method, cost, and token_usage from detection step
    #     detection_method = detected_result.get('detection_method', None) if isinstance(detected_result, dict) else None
    #     detected_cost = detected_result.get('cost', 0.0) if isinstance(detected_result, dict) else 0.0
    #     detected_token_usage = detected_result.get('token_usage', {}).get('total_tokens', 0) if isinstance(detected_result, dict) else 0.0
    #     result['detection_method'] = detection_method
    #     result['cost'] = detected_cost
    #     result['token_usage'] = detected_token_usage

    #     logger.debug(f"Institution name detection and validation result: {result}")
        
    #     return result

    def detect_and_validate_institution_names(self, prompt: str, conv_history: str = "") -> Dict[str, Optional[str]]:
        """
        Detects institution names from the prompt, validates them against the canonical list,
        and returns a dictionary including names, types, and metadata.
        """
        # 1Detect institutions + intent
        detected_result = self.detector.detect_institution_names(prompt, conv_history=conv_history)

        detected_names = detected_result.get('institution_names', [])
        intent = detected_result.get('intent', 'none')
        detection_method = detected_result.get('detection_method', None)
        detected_cost = detected_result.get('cost', 0.0)
        detected_token_usage = detected_result.get('token_usage', {}).get('total_tokens', 0) if isinstance(detected_result.get('token_usage'), dict) else 0.0

        # 2️ Validate against canonical list with types
        validated_institutions = self.validator.validate_institution_names(detected_names)
        self.validator.validate_intent(intent)

        # 3️ Build final detection result including types
        result = self.validator.build_detection_result(validated_institutions)
        result.update({
            "intent": intent,
            "detection_method": detection_method,
            "cost": detected_cost,
            "token_usage": detected_token_usage
        })

        logger.debug(f"Institution detection and validation result: {result}")
        return result