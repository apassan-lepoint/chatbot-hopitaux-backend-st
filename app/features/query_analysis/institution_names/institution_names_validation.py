""" 
institution_names_validation.py
---------------------------------
This module contains the InstitutionNamesValidator class responsible for validating detected institution names
and determining their types (public/private) based on a canonical list of institutions.
"""

from rapidfuzz import process
from typing import Optional, Dict, List, Any
from app.config.features_config import ERROR_MESSAGES
from app.features.query_analysis.institution_names.institution_names_model import HospitalInfo
from app.utility.functions.formatting_helpers import normalize_text
from app.utility.dicts_lists.institution_names_list import institution_names_list
from app.utility.dicts_lists.institution_names_type_dict import institution_names_type_dict 
from app.utility.functions.logging import get_logger


logger = get_logger(__name__)

class InstitutionNamesCheckException(Exception):
    pass
class InstitutionNamesValidator:
    """
    Validates detected institution names against a canonical list and determines their types.
    Attributes:
        institution_list (List[str]): List of canonical institution names for matching.
        institution_names_type_dict (Dict[str, str]): Dictionary mapping institution names to their types.
    Methods:    
        validate_institution_names(detected_names: List[str]) -> List[HospitalInfo]:
            Fuzzy matches detected names to canonical institutions and returns HospitalInfo objects.
        validate_intent(intent: Optional[str]) -> None:
            Validates that an intent was detected for institution names.
        build_validated_result(validated_institutions: List[Any]) -> Dict[str, object]:
            Builds the detection result dictionary for validated institution names.    
    """
    def __init__(self):
        # self.cleaned_to_original = {}
        self.institution_list = institution_names_list # Based on the current 2024 list of institution names 
        self.institution_names_type_dict = institution_names_type_dict # Based on the current 2024 list of institution names with types
        # self._load_institution_data()

    @staticmethod
    def validate_intent(intent: Optional[str]) -> None:
        """
        Validates that an intent was detected for institution names.
        Raises InstitutionNamesCheckException if intent is None.
        """
        if intent is None:
            logger.error("No intent detected for institution names.")
            raise InstitutionNamesCheckException(ERROR_MESSAGES["institution_name_intent_None"])
        logger.debug(f"Intent validated: {intent}")

        
    def _institution_name_normalize_part2(self, name):
        """
        Normalize institution names by expanding common abbreviations.
        """
        replace_map = {
            "ch ": "centre hospitalier ",
            "chu ": "centre hospitalier universitaire ",
            "chs ": "centre hospitalier spécialisé ",
            "chi ": "centre hospitalier intercommunal ",
            "chru ": "centre hospitalier régional universitaire "
            # Add more cases as needed
        }
        name = name.lower()
        for k, v in replace_map.items():
            name = name.replace(k, v)
        return normalize_text(name, mode="string_matching")


    def _get_institution_type(self, normalized_institution_name: str) -> str:
        """
        Looks up the institution type for a given institution name in the institution_names_type_dict.
        Returns 'public', 'private', or 'aucune correspondance'.
        """
        # normalized_name = self._normalize_name(self._clean_hospital_name(institution_name))
        institution_name_type = self.institution_names_type_dict.get(normalized_institution_name)
        if institution_name_type == "Public":
            return "public"
        elif institution_name_type == "Privé":
            return "private"
        return "aucune correspondance"


    def validate_institution_names(self, detected_names: List[str]) -> List[HospitalInfo]:
        """
        Fuzzy matches detected names to canonical institutions and returns HospitalInfo objects.
        """
        logger.debug(f"validate_institution_names called with detected_names={detected_names}")
        if not self.institution_list:
            logger.error("Canonical institution list is empty! Cannot validate detected names.")
            raise InstitutionNamesCheckException(ERROR_MESSAGES["general_ranking_error"])
        validated = []
        for name in detected_names:
            logger.debug(f"Processing detected name: '{name}'")
            intermediate_normalized_institution_name = normalize_text(name)
            normalized_institution_name = self._institution_name_normalize_part2(intermediate_normalized_institution_name)
            match = process.extractOne(normalized_institution_name, self.institution_list, score_cutoff=80)
            if not match:
                logger.debug(f"No valid match for '{name}' - raising error and stopping pipeline.")
                raise InstitutionNamesCheckException(ERROR_MESSAGES["institution_name_not_in_list"])
            matched_name = match[0]
            hospital_info = HospitalInfo(name=matched_name)
            hospital_info.type = self._get_institution_type(matched_name)
            validated.append(hospital_info)
            logger.debug(f"Validated '{name}' -> '{matched_name}' with type '{hospital_info.type}'")
        logger.debug(f"Validation result: {validated}")
        return validated
    

    def build_validated_result(self, validated_institutions: List[Any]) -> Dict[str, object]:
        """
        Builds the detection result dictionary for validated institution names.
        """
        # Success case: valid HospitalInfo objects
        if validated_institutions and all(hasattr(h, "name") for h in validated_institutions):
            logger.info(f"Specific institutions mentioned: {', '.join([h.name for h in validated_institutions])}")
            return {"institutions": validated_institutions, "institution_name_mentioned": True}
        # Error case: error string
        if validated_institutions and isinstance(validated_institutions[0], str):
            return {"institutions": None, "institution_name_mentioned": False, "error": validated_institutions[0]}
        # Fallback case: nothing detected
        logger.info("No specific institution detected")
        return {"institutions": None, "institution_name_mentioned": False, "error": "No institution detected"}
