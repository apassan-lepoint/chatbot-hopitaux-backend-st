""" 
institution_type_validation.py
----------------------------------
Module for validating and normalizing institution types.
"""

from typing import Optional
from app.config.features_config import INSTITUTION_TYPE_MAPPING, INSTITUTION_TYPE_CODES

class InstitutionTypeValidator:
    """
    Class to validate and normalize institution types. 
    Attributes:
        INSTITUTION_TYPE_MAPPING (dict): A mapping of institution type strings to their normalized forms.
        INSTITUTION_TYPE_CODES (dict): A mapping of institution type strings to their corresponding codes.
    Methods:
        normalize_institution_type(institution_type: str) -> str: Normalizes the institution type string.
        get_institution_type_code(institution_type: str) -> int: Returns the code for the institution type.
        is_public_institution(institution_type: Optional[str]) -> bool: Checks if the institution type is public.
        is_private_institution(institution_type: Optional[str]) -> bool: Checks if the institution type is private.
        is_institution_type_valid(institution_type
    """
    def normalize_institution_type(self, institution_type: str) -> str:
        if not institution_type or institution_type in ["no match", "aucune correspondance"]:
            return "aucune correspondance"
        type_lower = institution_type.lower().strip()
        return INSTITUTION_TYPE_MAPPING.get(type_lower, "aucune correspondance")


    def get_institution_type_code(self, institution_type: str) -> int:
        normalized = self.normalize_institution_type(institution_type)
        if normalized == "Public":
            return INSTITUTION_TYPE_CODES["public"]
        elif normalized == "Privé":
            return INSTITUTION_TYPE_CODES["private"]
        else:
            return INSTITUTION_TYPE_CODES["no_match"]


    def is_public_institution(self, institution_type: Optional[str]) -> bool:
        """
        Checks if the institution type is public.
        """
        return self.normalize_institution_type(institution_type) == "Public"


    def is_private_institution(self, institution_type: Optional[str]) -> bool:
        """
        Checks if the institution type is private.
        """
        return self.normalize_institution_type(institution_type) == "Privé"


    def is_institution_type_valid(self, institution_type: str) -> bool:
        """
        Checks if the institution type is valid.
        """
        return self.normalize_institution_type(institution_type) != "aucune correspondance"
