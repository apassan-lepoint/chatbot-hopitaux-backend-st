from app.utility.logging import get_logger
from typing import Optional, Dict, List, Any
from rapidfuzz import process
from app.config.features_config import ERROR_MESSAGES
from app.config.file_paths_config import PATHS
import pandas as pd
from app.features.query_analysis.institution_names.institution_names_model import HospitalInfo


logger = get_logger(__name__)

class InstitutionNamesCheckException(Exception):
    """
    Custom exception for institution names validation checks.
    """
    pass
class InstitutionNamesValidator:
    """
    Responsible for validating detected institution names and determining type.
    Works with a canonical list of dicts: [{"nom": ..., "ville": ..., "departement": ..., "type": ...}]
    """
    def __init__(self):
        self.cleaned_to_original = {}
        self.institution_list = []
        self._load_institution_data()

    def _load_institution_data(self):
        """
        Loads the hospital DataFrame and builds a list of (cleaned_name, original_full_name) tuples for matching.
        """
        institution_df = pd.read_excel(PATHS["hospital_coordinates_path"])
        self.match_tuples = []  # List of (cleaned_name, original_full_name)
        for original in institution_df.iloc[:, 0]:
            if not isinstance(original, str):
                continue
            cleaned = original.split(",")[0].strip()
            if cleaned not in ["CHU", "CH"]:
                self.match_tuples.append((cleaned, original))
        self.institution_list = list(set([t[0] for t in self.match_tuples]))

    def format_hospital_list(self, institution_df) -> str:
        institution_list = [element.split(",")[0] for element in institution_df.iloc[:, 0]]
        institution_list = list(set(institution_list))
        institution_list = [element for element in institution_list if element != "CHU"]
        institution_list = [element for element in institution_list if element != "CH"]
        return institution_list

    def clean_etablissement_column(self, df):
        df = df.copy()
        df["Etablissement_clean"] = df["Etablissement"].apply(lambda x: x.split(",")[0].strip() if isinstance(x, str) else x)
        df = df[~df["Etablissement_clean"].isin(["CHU", "CH"])]
        return df

    def get_institution_type_from_df(self, institution_name: str) -> str:
        """
        Looks up the institution type for a given institution name in the hospital coordinates DataFrame.
        Returns 'public', 'private', or 'aucune correspondance'.
        """
        institutions_df = pd.read_excel(PATHS["hospital_coordinates_path"])
        institutions_df = self.clean_etablissement_column(institutions_df)
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
        For each detected name, fuzzy match on cleaned_name, but always return the full original Etablissement value.
        """
        logger.debug(f"validate_institution_names called with detected_names={detected_names} and institution_list length={len(self.institution_list)})")
        if not self.institution_list:
            logger.error("Canonical institution list is empty! Cannot validate detected names.")
            return ["Canonical institution list is empty."]
        validated = []
        for name in detected_names:
            logger.debug(f"Processing detected name: '{name}'")
            match = process.extractOne(name, self.institution_list, score_cutoff=80)
            if match:
                cleaned_name = match[0]
                # Find all original_full_names for this cleaned_name
                canonical_names = [orig for (clean, orig) in self.match_tuples if clean == cleaned_name]
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
        if validated_institutions:
            logger.info(f"Specific institutions mentioned: {', '.join([h.name for h in validated_institutions])}")
            return {"institutions": validated_institutions, "institution_name_mentioned": True}
        else:
            logger.info("No specific institution detected")
            return {"institutions": None, "institution_name_mentioned": False, "error": "No institution detected"}
        

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
    #             "institution_name_mentioned": True,
    #             "institution_type": None
    #         }
    #     else:
    #         logger.info("No specific institution detected, using fallback type")
    #         return {
    #             "institution_names": None,
    #             "institution_name_mentioned": False,
    #             "institution_type": institution_type
    #         }