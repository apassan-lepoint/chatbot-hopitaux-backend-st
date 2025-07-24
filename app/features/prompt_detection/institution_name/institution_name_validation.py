from app.utility.logging import get_logger
from typing import Optional, Dict

logger = get_logger(__name__)

class InstitutionNameValidator:
    """
    Responsible for validating detected institution name and determining type.
    """
    def __init__(self, institution_list: str = ""):
        self.institution_list = institution_list

    def set_institution_list(self, institution_list: str) -> None:
        self.institution_list = institution_list
        logger.debug(f"Institution list updated with {len(institution_list.split(','))} institutions")

    def validate_institution_name(self, detected_name: str) -> bool:
        """
        Checks if the detected institution name is in the known institution list.
        Args:
            detected_name (str): The name detected by the detector
        Returns:
            bool: True if valid, False otherwise
        """
        institution_names = [name.strip() for name in self.institution_list.split(",")]
        is_valid = detected_name in institution_names
        logger.debug(f"Validation result for '{detected_name}': {is_valid}")
        return is_valid

    def build_detection_result(self, detected_name: str, institution_type: Optional[str] = None) -> Dict[str, Optional[str]]:
        """
        Builds the result dictionary for the detection process.
        Args:
            detected_name (str): The name detected by the detector
            institution_type (str, optional): The type if no specific institution
        Returns:
            dict: Result with institution_name, institution_mentioned, institution_type
        """
        if self.validate_institution_name(detected_name):
            logger.info(f"Specific institution mentioned: {detected_name}")
            return {
                "institution_name": detected_name,
                "institution_mentioned": True,
                "institution_type": None
            }
        else:
            logger.info("No specific institution detected, using fallback type")
            return {
                "institution_name": None,
                "institution_mentioned": False,
                "institution_type": institution_type
            }
