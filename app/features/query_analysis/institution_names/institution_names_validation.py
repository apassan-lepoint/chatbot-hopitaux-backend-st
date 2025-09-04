from app.utility.logging import get_logger
from typing import Optional, Dict, List
from rapidfuzz import process, fuzz

logger = get_logger(__name__)

class InstitutionNamesValidator:
    """
    Responsible for validating detected institution name and determining type.
    It checks if the detected institution name is in a predefined list of known institutions.   
    Attributes:
        institution_list (str): Comma-separated list of known institution names.
    Methods:
        set_institution_list(institution_list: str) -> None:
            Updates the institution list used for validation.
        validate_institution_names(detected_name: str) -> bool:
            Checks if the detected institution name is in the known institution list.
        build_detection_result(detected_name: str, institution_type: Optional[str] = None) -> Dict[str, Optional[str]]:
            Builds the result dictionary for the detection process. 
    """
    # def __init__(self, institution_list: str = ""):
    #     self.institution_list = institution_list

    # def set_institution_list(self, institution_list: str) -> None:
    #     """
    #     Updates the institution list used for validation.
    #     """
    #     self.institution_list = institution_list
    #     logger.debug(f"Institution list updated with {len(institution_list.split(','))} institutions")

    # def validate_institution_names(self, detected_name: str) -> bool:
    #     """
    #     Checks if the detected institution name is in the known institution list.
    #     """
    #     institution_namess = [name.strip() for name in self.institution_list.split(",")]
    #     is_valid = detected_name in institution_namess
    #     logger.debug(f"Validation result for '{detected_name}': {is_valid}")
    #     return is_valid

    # def build_detection_result(self, detected_name: str, institution_type: Optional[str] = None) -> Dict[str, Optional[str]]:
    #     """
    #     Builds the result dictionary for the detection process.
    #     """
    #     if self.validate_institution_names(detected_name):
    #         logger.info(f"Specific institution mentioned: {detected_name}")
    #         return {
    #             "institution_names": detected_name,
    #             "institution_mentioned": True,
    #             "institution_type": None
    #         }
    #     else:
    #         logger.info("No specific institution detected, using fallback type")
    #         return {
    #             "institution_names": None,
    #             "institution_mentioned": False,
    #             "institution_type": institution_type
    #         }


    """
    Validates detected institution names against a canonical list with types,
    using fuzzy matching.
    """

    def validate_institution_names(self, detected_names: List[str], institution_list: Dict[str, str]) -> List[Dict[str, Optional[str]]]:
        """
        Validates a list of detected institution names against the canonical institution_list.
        institution_list: Dict[name -> type], e.g. {"CHU de Lille": "public"}

        Returns a list of dictionaries:
        [{"name": <validated_name>, "type": <institution_type>}]
        """
        validated = []
        for name in detected_names:
            match = process.extractOne(name, list(institution_list.keys()), score_cutoff=80)
            if match:
                validated.append({"name": match[0], "type": institution_list[match[0]]})
                logger.debug(f"Validated '{name}' -> '{match[0]}' ({institution_list[match[0]]})")
            else:
                logger.debug(f"No valid match for '{name}'")
        return validated
    
    def build_detection_result(self, validated_institutions: List[Dict[str, Optional[str]]]) -> Dict[str, Optional[List[Dict[str, Optional[str]]]]]:
        """
        Builds the detection result dictionary including institution types.
        Returns:
        {
            "institutions": [{"name": ..., "type": ...}, ...],
            "institution_mentioned": bool
        }
        """
        if validated_institutions:
            names_str = ", ".join([inst["name"] for inst in validated_institutions])
            logger.info(f"Specific institutions mentioned: {names_str}")
            return {
                "institutions": validated_institutions,
                "institution_mentioned": True
            }
        else:
            logger.info("No specific institution detected")
            return {
                "institutions": None,
                "institution_mentioned": False
            }