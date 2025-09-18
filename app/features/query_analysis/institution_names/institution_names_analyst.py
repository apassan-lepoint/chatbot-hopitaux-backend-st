""" 
institution_names_analyst.py
---------------------------------
This module contains the InstitutionNamesAnalyst class which integrates detection and validation of institution names from user prompts.
"""

from typing import Optional, Dict
from app.features.query_analysis.institution_names.institution_names_detection import InstitutionNamesDetector
from app.features.query_analysis.institution_names.institution_names_validation import InstitutionNamesValidator
from app.utility.logging import get_logger


logger = get_logger(__name__)


class InstitutionNamesAnalyst:
    """
    Class to analyze, detect, and validate institution names from user prompts.
    Attributes:
        detector (InstitutionNamesDetector): Instance to detect institution names.
        validator (InstitutionNamesValidator): Instance to validate detected names.     
    Methods:
        detect_and_validate_institution_names(prompt: str, conv_history: str = "") -> Dict[str, Optional[str]]:
            Detects and validates institution names from the prompt and returns a structured result.
    """
    def __init__(self, model=None):
        self.detector = InstitutionNamesDetector(model)
        self.validator = InstitutionNamesValidator()


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