""" 
location_validation.py
-------------------
This module defines the LocationValidator class, which validates user input for non-French cities.
"""

import re
from rapidfuzz import process
from app.config.features_config import ERROR_MESSAGES
from app.utility.functions.formatting_helpers import normalize_text
from app.utility.functions.logging import get_logger
from app.utility.dicts_lists.geo_dict import valid_locations_dict


logger = get_logger(__name__)

class LocationCheckException(Exception):
    pass


class LocationValidator:
    """
    Class to validate user input for non-French cities.
    Attributes:
        llm_handler_service: Service for handling LLM interactions (optional).
        detector: Instance of LocationDetector for location detection.
    Methods:
        check(user_input, conv_history=""): Checks for non-French cities in user input.
    """
    def __init__(self, detector, llm_handler_service=None):
        logger.info("Initializing LocationValidator")
        self.llm_handler_service = llm_handler_service
        self.detector = detector
        self.valid_locations = valid_locations_dict


    
    def _fuzzy_match_value(self, value: str, valid_list: list, score_cutoff=80):
        normalized_value = normalize_text(value)
        logger.debug(f"Fuzzy matching '{normalized_value}' against {len(valid_list)} candidates (score_cutoff={score_cutoff})")
        match = process.extractOne(normalized_value, valid_list, score_cutoff=score_cutoff)
        if match:
            logger.debug(f"Fuzzy match result: input='{normalized_value}', match='{match[0]}', score={match[1]}")
            return match[0]
        logger.debug(f"Fuzzy match failed: input='{normalized_value}', no match found above cutoff")
        return None
    

    def check(self, user_input, conv_history=""):
        """
        Checks for non-French cities in user input. Raises LocationCheckException if foreign or ambiguous.
        Returns a dict with validated location fields if valid, else empty dict.
        """
        logger.debug(f"Location check called: user_input={user_input}, conv_history={conv_history}")
        if not self.detector:
            logger.warning("LocationValidator.check: detector is missing, skipping location validation.")
            return  {}
        
        location_result = self.detector.detect_location(user_input, conv_history)
        location_status_type = self.detector.get_location_status_type(location_result.get('status_code') if isinstance(location_result, dict) else location_result)
        
        if location_status_type == "foreign":
            raise LocationCheckException(ERROR_MESSAGES["non_french_cities"])
        
        if location_status_type == "ambiguous":
            raise LocationCheckException(ERROR_MESSAGES["ambiguous_location"])

        detected_location = location_result.get("location", {})
        if not detected_location:
            return {}

        # Ensure detected_location is a dict of lists for each location type
        logger.debug(f"Raw detected_location: {detected_location} (type={type(detected_location)})")
        normalized_location = {k: [] for k in ["region", "department", "city_commune", "postal_code"]}
        # Accept both a single dict and a list of dicts
        if isinstance(detected_location, dict):
            detected_location = [detected_location]
        if isinstance(detected_location, list):
            for loc in detected_location:
                k = loc.get("type")
                v = loc.get("value")
                if k in normalized_location and v:
                    if isinstance(v, list):
                        normalized_location[k].extend(v)
                    else:
                        normalized_location[k].append(v)
        logger.debug(f"Normalized location: {normalized_location}")
        validated_location = normalized_location

        for key in ["region", "city_commune"]:
            for value in validated_location.get(key, []):
                match = self._fuzzy_match_value(value, self.valid_locations.get(key, []), score_cutoff=80)
                if match:
                    validated_location[key] = [match]
                    logger.debug(f"Fuzzy match successful for {key}: {match}")
                else:
                    logger.debug(f"Fuzzy match failed for {key}: {value}")
                    raise LocationCheckException(f"{key} '{value}' not valid (fuzzy match failed)")
        for key in ["department", "postal_code"]:
            for value in validated_location.get(key, []):
                if value in self.valid_locations.get(key, []):
                    validated_location[key] = [value]
                else:
                    raise LocationCheckException(f"{key} '{value}' not in valid list")
        logger.debug(f"Validated location: {validated_location}")
        return validated_location