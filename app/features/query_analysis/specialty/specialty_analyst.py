""" 
specialty_analyst.py
------------------------------
Handles specialty detection and validation using LLMs.
"""

from typing import Optional, Dict, List
from .specialty_detection import SpecialtyDetector
from .specialty_validation import SpecialtyValidator
from app.utility.functions.logging import get_logger


logger = get_logger(__name__)


class SpecialtyAnalyst:
    """
    Class to handle specialty detection and validation.
    Attributes:
        detector (SpecialtyDetector): Instance for specialty detection.
        validator (SpecialtyValidator): Instance for specialty validation.  
    Methods:
        detect_and_validate_specialty(prompt: str, conv_history: str = "") -> Dict[str[str, Optional[str]]:
            Detects and validates specialty from the prompt and returns a result dict.
    """
    def __init__(self, model):
        self.detector = SpecialtyDetector(model)
        self.validator = SpecialtyValidator()

    
    def detect_and_validate_specialty(self, prompt: str, conv_history: str = "") -> Dict[str, Optional[str]]:
        """
        Detects the specialty from the prompt, validates and maps it, and returns the result dict.
        Only handles specialty logic. Returns a dict with cost, detection_method, and token_usage.
        """
        result = {}
       
        # Detect specialty (LLM raw output)
        detected_result = self.detector.detect_specialty(prompt, conv_history)
        detected_specialty = detected_result.get('specialty', detected_result.get('content', detected_result)) if isinstance(detected_result, dict) else detected_result
       
        # Validate and map using validator
        mapped = self.validator.validate_specialty(detected_specialty)
        
        # Return string if only one specialty, list if multiple
        if isinstance(mapped, list):
            if len(mapped) == 1:
                result['specialty'] = mapped[0]
            else:
                result['specialty'] = mapped
        else:
            result['specialty'] = mapped
        
        # Extract detection_method, cost, and token_usage from detection step
        detection_method = detected_result.get('detection_method', None) if isinstance(detected_result, dict) else None
        detected_cost = detected_result.get('cost', 0.0) if isinstance(detected_result, dict) else 0.0
        detected_token_usage = detected_result.get('total_tokens', 0) if isinstance(detected_result, dict) else 0.0
        result['detection_method'] = detection_method
        result['cost'] = detected_cost
        result['token_usage'] = detected_token_usage
        
        logger.debug(f"Specialty detection and validation result: {result}")
        
        return result
