from typing import Optional

class InstitutionTypeValidator:
    """
    Handles validation and normalization of institution type values.
    """
    TYPE_MAPPING = {
        "aucune correspondance": "aucune correspondance",
        "no match": "aucune correspondance",
        "public": "Public",
        "private": "Privé",
        "privé": "Privé",
        "prive": "Privé",
        "publique": "Public",
        "privée": "Privé"
    }
    TYPE_CODES = {
        "no_match": 0,
        "public": 1,
        "private": 2
    }

    def __init__(self, institution_list: str):
        self.institution_list = institution_list

    def is_valid_institution(self, institution_name: str) -> bool:
        if not institution_name or institution_name == "aucune correspondance":
            return False
        institution_names = [name.strip() for name in self.institution_list.split(",")]
        return institution_name in institution_names

    def normalize_institution_type(self, institution_type: str) -> str:
        if not institution_type or institution_type in ["no match", "aucune correspondance"]:
            return "aucune correspondance"
        type_lower = institution_type.lower().strip()
        return self.TYPE_MAPPING.get(type_lower, "aucune correspondance")

    def get_institution_type_code(self, institution_type: str) -> int:
        normalized = self.normalize_institution_type(institution_type)
        if normalized == "Public":
            return self.TYPE_CODES["public"]
        elif normalized == "Privé":
            return self.TYPE_CODES["private"]
        else:
            return self.TYPE_CODES["no_match"]

    def is_public_institution(self, institution_type: Optional[str]) -> bool:
        return self.normalize_institution_type(institution_type) == "Public"

    def is_private_institution(self, institution_type: Optional[str]) -> bool:
        return self.normalize_institution_type(institution_type) == "Privé"

    def is_institution_type_valid(self, institution_type: str) -> bool:
        return self.normalize_institution_type(institution_type) != "aucune correspondance"
