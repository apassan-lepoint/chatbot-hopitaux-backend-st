from typing import Optional, Dict
from .institution_type_detection import InstitutionTypeDetector
from .institution_type_validation import InstitutionTypeValidator
from app.utility.logging import get_logger

logger = get_logger(__name__)

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
        detect_and_validate_institution_type(prompt: str, conv_history: str = "") -> Dict[str, Optional[str]]:
            Detects the institution type from the prompt and conversation history, validates it,
            and returns a summary dictionary containing the raw institution type, normalized institution type,
            and validation status.  
    """
    def __init__(self, model=None):
        self.model = model
        self.detector = InstitutionTypeDetector(model)
        self.validator = InstitutionTypeValidator()


    def detect_and_validate_institution_type(self, prompt: str, conv_history: str = "") -> Dict[str, Optional[str]]:
        """
        Detects institution type, validates, and returns a summary dict with cost, detection_method, and token_usage.
        """
        result = {}
        
        # Detect and validate institution type
        detected_result = self.detector.detect_institution_type(prompt, conv_history)
        detected_institution_type = detected_result.get('institution_type', detected_result.get('content', detected_result)) if isinstance(detected_result, dict) else detected_result
        institution_type = self.validator.normalize_institution_type(detected_institution_type)
        result['institution_type'] = institution_type

        # Extract detection_method, cost, and token_usage from detection step
        detection_method = detected_result.get('detection_method', None) if isinstance(detected_result, dict) else None
        detected_cost = detected_result.get('cost', 0.0) if isinstance(detected_result, dict) else 0.0
        # detected_token_usage = detected_result.get('total_tokens', 0.0) if isinstance(detected_result, dict) else 0.0
        detected_token_usage = (detected_result.get('token_usage', 0).get('total_tokens', 0)
                                if isinstance(detected_result, dict) and isinstance(detected_result.get('token_usage', 0), dict)
                                else detected_result.get('token_usage', 0) if isinstance(detected_result, dict) else 0.0
                            )
        result['detection_method'] = detection_method
        result['cost'] = detected_cost
        result['token_usage'] = detected_token_usage

        logger.debug(f"Institution type detection and validation result: {result}")

        return result