from typing import List
from app.utility.specialty_dicts_lists import specialty_categories_dict as default_dict
import unidecode

class SpecialtyValidator:
    """
    Handles validation and normalization of specialty values.
    Attributes:
        specialty_list (List[str]): A list of valid specialty names.
        specialty_categories_dict (dict): A dictionary mapping specialties to their categories.
    Methods:
        validate_specialty(raw_specialty: str) -> List[str]:
            Validates and normalizes the specialty string, returning a list of recognized specialties.
    """
    def __init__(self, specialty_list: List[str], specialty_categories_dict=None):
        # Normalize specialty list: lowercase, no accents, strip
        self.specialty_list = [unidecode.unidecode(s).lower().strip() for s in specialty_list]
        self.specialty_categories_dict = specialty_categories_dict or default_dict

    def _is_no_match(self, specialty: str) -> bool:
        """Check if specialty string means no match."""
        return not specialty or specialty.lower() in {"no specialty match", "aucune correspondance", "no match", ""}
    

    def _normalize_specialty_format(self, specialty: str) -> str:
        """Normalize specialty string for processing."""
        if not specialty:
            return "no specialty match"
        specialty = specialty.replace("plusieurs correspondances:", "multiple matches:")
        if specialty == 'aucune correspondance':
            specialty = "no specialty match"
        if ',' in specialty and not specialty.startswith('multiple matches:'):
            specialty = 'multiple matches: ' + specialty
        return specialty.strip()

    
    def _extract_specialty_list(self, specialty: str) -> List[str]:
        """Extract list of individual specialties from formatted specialty string."""
        if not specialty:
            return []
        normalized = self._normalize_specialty_format(specialty)
        if ',' in normalized or normalized.startswith('multiple matches:'):
            if normalized.startswith('multiple matches:'):
                specialty_list = normalized.replace('multiple matches:', '').strip()
            else:
                specialty_list = normalized
            return [s.strip() for s in specialty_list.split(',') if s.strip()]
        else:
            return [normalized] if normalized and not self._is_no_match(normalized) else []

    def validate_specialty(self, raw_specialty: str) -> List[str]:
        """
        Runs normalization and extraction for a specialty string.
        """
        normalized_specialty = self._normalize_specialty_format(raw_specialty)
        specialty_list = self._extract_specialty_list(normalized_specialty)
        return specialty_list