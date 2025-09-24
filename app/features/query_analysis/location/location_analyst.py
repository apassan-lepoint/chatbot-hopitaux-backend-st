""" 
location_analyst.py
----------------
This module defines the LocationAnalyst class, which detects and validates location names from user prompts.
"""

from app.config.features_config import ERROR_MESSAGES
from app.features.query_analysis.location.location_detection import LocationDetector
from app.features.query_analysis.location.location_validation import LocationValidator, LocationCheckException
from app.utility.functions.logging import get_logger


logger = get_logger(__name__)


class MultipleLocationsDetectedException(Exception):
    pass


class LocationAnalyst:
    """
    Class to detect and validate location names from user prompts.
    Attributes:
        detector (LocationDetector): Component to detect location names.
        validator (LocationValidator): Component to validate detected location names.
    Methods:
        detect_and_validate_location(prompt, conv_history=""):
            Detects and validates the location from the prompt, returning both location and detection status.   
    """
    def __init__(self, llm_handler_service=None, model=None):
        logger.info("Initializing LocationAnalyst")
        self.detector = LocationDetector(model)
        self.validator = LocationValidator(self.detector, llm_handler_service)


    def detect_and_validate_location(self, prompt: str, conv_history: str = ""):
        """
        Detects and validates the location from the prompt, returning:
        - location (dict with region, department, city_commune, postal_code)
        - location_detected (bool)
        - status_code, detection_method, cost, token_usage
        Raises LocationCheckException if foreign or ambiguous.
        """
        result = {}

        # Step 1: Detect location using the LLM detector
        logger.info(f"Calling LocationDetector.detect_location with prompt: {prompt!r}, conv_history: {conv_history!r}")
        detected_result = self.detector.detect_location(prompt, conv_history)
        logger.info(f"Raw detected_result from LocationDetector: {detected_result!r}")

        # Step 2: Validate location (may raise exception if foreign/ambiguous)
        validated_location = self.validator.check(prompt, conv_history)  # returns dict of validated fields

        # Step 3: Determine if a location was detected
        detected_location_bool = bool(
            validated_location
            and any(validated_location.get(k) for k in ["region","department","city_commune","postal_code"])
        )

        # Step 3a: Check for multiple locations per key
        for key in ["region","department","department_number","city_commune","postal_code"]:
            values = validated_location.get(key, [])
            if len(values) > 1:
                logger.error(f"Multiple locations detected for key '{key}'; stopping pipeline.")
                raise MultipleLocationsDetectedException(
                    ERROR_MESSAGES["too_many_locations_detected"]
                )

        # Step 4: Extract metadata
        detected_status_code = detected_result.get('status_code') if isinstance(detected_result, dict) else None
        detection_method = detected_result.get('detection_method') if isinstance(detected_result, dict) else None
        detected_cost = detected_result.get('cost', 0.0) if isinstance(detected_result, dict) else 0.0
        detected_token_usage = (
            detected_result.get('token_usage', 0).get('total_tokens', 0)
            if isinstance(detected_result, dict) and isinstance(detected_result.get('token_usage', 0), dict)
            else detected_result.get('token_usage', 0) if isinstance(detected_result, dict) else 0.0
        )

        # Step 5: Assemble final result
        result['location'] = validated_location if detected_location_bool else None
        result['location_detected'] = detected_location_bool
        result['status_code'] = detected_status_code
        result['detection_method'] = detection_method
        result['cost'] = detected_cost
        result['token_usage'] = detected_token_usage

        logger.debug(f"Location detection and validation result: {result}")
        # After validation, log final result
        logger.debug(f"LocationAnalyst: final validation result: {result}")
        return result