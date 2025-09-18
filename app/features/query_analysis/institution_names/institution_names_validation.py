""" 
institution_names_validation.py
---------------------------------
This module contains the InstitutionNamesValidator class responsible for validating detected institution names
and determining their types (public/private) based on a canonical list of institutions.
"""

import pandas as pd
from rapidfuzz import process
import re
from typing import Optional, Dict, List, Any
from app.config.features_config import ERROR_MESSAGES
from app.config.file_paths_config import PATHS
from app.features.query_analysis.institution_names.institution_names_model import HospitalInfo
from app.utility.logging import get_logger


logger = get_logger(__name__)

class InstitutionNamesCheckException(Exception):
    pass
class InstitutionNamesValidator:
    """
    Class to validate detected institution names against a canonical list and determine their types.    
    Attributes:
        cleaned_to_original (Dict[str, str]): Mapping from cleaned institution names to original full names.
        institution_list (List[str]): List of cleaned institution names for fuzzy matching. 
        match_tuples (List[Tuple[str, str]]): List of tuples (normalized_cleaned_name, original_full_name) for matching.
    Methods:
        _clean_hospital_name(etablissement: str) -> str:
            Cleans the hospital name according to specified rules.
        _normalize_name(name: str) -> str:
            Normalizes the name by removing articles and extra spaces for robust matching.
        _load_institution_data() -> None:
            Loads the hospital DataFrame and builds the matching tuples and institution list.
        validate_institution_names(detected_names: List[str]) -> List[HospitalInfo]:
            Validates detected institution names and returns a list of HospitalInfo objects.
        validate_intent(intent: Optional[str]) -> None:
            Validates that an intent was detected for institution names.
        build_detection_result(validated_institutions: List[Any]) -> Dict[str, object]:
            Builds the detection result dictionary for validated institution names.     
    """
    def __init__(self):
        self.cleaned_to_original = {}
        self.institution_list = []
        self._load_institution_data()


    def _clean_hospital_name(self, institution: str) -> str:
        """
        Cleans the hospital name according to the following rules:
        - If the name starts with CH, CHU, CHR, or CHRU (case-insensitive), keep up to (but not including) the first parentheses with exactly two digits.
        - Otherwise, keep up to the first comma.
        """
        if not isinstance(institution, str):
            return institution
        institution = institution.strip()
        if re.match(r'^(CHU?|CHR?U?)\b', institution, re.IGNORECASE):
            match = re.search(r'\([0-9]{2}\)', institution)
            if match:
                start = match.start()
                return institution[:start].strip()
            else:
                return institution  # fallback: return full string if no match
        else:
            return institution.split(',')[0].strip()


    def _normalize_name(self, name: str) -> str:
        """
        Removes common French articles and extra spaces from the name for robust matching.
        """
        if not isinstance(name, str):
            return name
        # Remove articles and commas, collapse spaces
        name = re.sub(r"\b(de|du|des|la|le|les|l')\b", "", name, flags=re.IGNORECASE)
        name = name.replace(",", " ")
        name = re.sub(r"\s+", " ", name)
        return name.strip().lower()


    def _load_institution_data(self):
        """
        Loads the hospital DataFrame and builds a list of (normalized_cleaned_name, original_full_name) tuples for matching.
        """
        institution_df = pd.read_excel(PATHS["hospital_coordinates_path"])
        self.match_tuples = []  # List of (normalized_cleaned_name, original_full_name)
        for original in institution_df.iloc[:, 0]:
            if not isinstance(original, str):
                continue
            cleaned = self._clean_hospital_name(original)
            normalized = self._normalize_name(cleaned)
            if normalized not in [self._normalize_name(x) for x in ["CHU", "CH", "CHR", "CHRU"]]:
                self.match_tuples.append((normalized, original))
        self.institution_list = list(set([t[0] for t in self.match_tuples]))


    def _clean_etablissement_column(self, df):
        df = df.copy()
        df["Etablissement_clean"] = df["Etablissement"].apply(lambda x: self._normalize_name(self._clean_hospital_name(x)))
        df = df[~df["Etablissement_clean"].isin([self._normalize_name(x) for x in ["CHU", "CH", "CHR", "CHRU"]])]
        return df


    def get_institution_type_from_df(self, institution_name: str) -> str:
        """
        Looks up the institution type for a given institution name in the hospital coordinates DataFrame.
        Returns 'public', 'private', or 'aucune correspondance'.
        """
        institutions_df = pd.read_excel(PATHS["hospital_coordinates_path"])
        institutions_df = self._clean_etablissement_column(institutions_df)
        row = institutions_df[institutions_df["Etablissement_clean"].str.lower().str.strip() == institution_name.lower().strip()]
        if not row.empty:
            privacite = row.iloc[0]["privacité"]
            if privacite == "Public":
                return "public"
            elif privacite == "Privé":
                return "private"
        return "aucune correspondance"


    def validate_institution_names(self, detected_names: List[str]) -> List[HospitalInfo]:
        """
        For each detected name, fuzzy match on normalized_cleaned_name, but always return the full original Etablissement value.
        """
        logger.debug(f"validate_institution_names called with detected_names={detected_names} and institution_list length={len(self.institution_list)})")
        if not self.institution_list:
            logger.error("Canonical institution list is empty! Cannot validate detected names.")
            return ["Canonical institution list is empty."]
        validated = []
        for name in detected_names:
            logger.debug(f"Processing detected name: '{name}'")
            normalized_name = self._normalize_name(self._clean_hospital_name(name))
            match = process.extractOne(normalized_name, self.institution_list, score_cutoff=80)
            if match:
                cleaned_name = match[0]
                # Find all original_full_names for this normalized_cleaned_name
                canonical_names = [orig for (norm, orig) in self.match_tuples if norm == cleaned_name]
                for canonical_name in canonical_names:
                    hospital_info = HospitalInfo(name=canonical_name)
                    hospital_info.type = self.get_institution_type_from_df(cleaned_name)
                    validated.append(hospital_info)
                    logger.debug(f"Validated '{name}' -> '{canonical_name}' with type '{hospital_info.type}'")
            else:
                logger.debug(f"No valid match for '{name}' - raising error and stopping pipeline.")
                raise InstitutionNamesCheckException(ERROR_MESSAGES["institution_name_not_in_list"])
        logger.debug(f"Validation result: {validated}")
        return validated
    

    def validate_intent(self, intent: Optional[str]) -> None:
        """
        Validates that an intent was detected for institution names.
        Raises InstitutionNamesCheckException if intent is None.
        """
        if intent is None:
            logger.error("No intent detected for institution names.")
            raise InstitutionNamesCheckException(ERROR_MESSAGES["institution_name_intent_None"])
        logger.debug(f"Intent validated: {intent}")


    def build_detection_result(self, validated_institutions: List[Any]) -> Dict[str, object]:
        """
        Builds the detection result dictionary for validated institution names.
        Returns:
        { "institutions": [HospitalInfo objects], "institution_name_mentioned": bool}
        """
        if validated_institutions and isinstance(validated_institutions[0], str) and validated_institutions[0].startswith("No valid match"):
            return {"institutions": None, "institution_name_mentioned":True, "error": validated_institutions[0]}
        # Only set institution_name_mentioned True if all are real HospitalInfo objects
        if validated_institutions and all(hasattr(h, "name") for h in validated_institutions):
            logger.info(f"Specific institutions mentioned: {', '.join([h.name for h in validated_institutions])}")
            return {"institutions": validated_institutions, "institution_name_mentioned": True}
        else:
            logger.info("No specific institution detected")
            return {"institutions": None, "institution_name_mentioned": False, "error": "No institution detected"}

    # def format_hospital_list(self, institution_df) -> str:
    #     institution_list = [self._normalize_name(self._clean_hospital_name(element)) for element in institution_df.iloc[:, 0]]
    #     institution_list = list(set(institution_list))
    #     institution_list = [element for element in institution_list if element not in [self._normalize_name(x) for x in ("CHU", "CH", "CHR", "CHRU")]]
    #     return institution_list