from typing import Optional, List
from app.utility.specialty_dicts_lists import specialty_categories_dict as default_dict


class SpecialtyValidator:
    def __init__(self, specialty_list: List[str], specialty_categories_dict=None):
        self.specialty_list = specialty_list
        self.specialty_categories_dict = specialty_categories_dict or default_dict

    def normalize_specialty_format(self, specialty: str) -> str:
        """Normalize specialty string for processing."""
        if not specialty:
            return "no specialty match"
        specialty = specialty.replace("plusieurs correspondances:", "multiple matches:")
        if specialty == 'aucune correspondance':
            specialty = "no specialty match"
        if ',' in specialty and not specialty.startswith('multiple matches:'):
            specialty = 'multiple matches: ' + specialty
        return specialty.strip()

    def extract_specialty_list(self, specialty: str) -> List[str]:
        """Extract list of individual specialties from formatted specialty string."""
        if not specialty:
            return []
        normalized = self.normalize_specialty_format(specialty)
        if ',' in normalized or normalized.startswith('multiple matches:'):
            if normalized.startswith('multiple matches:'):
                specialty_list = normalized.replace('multiple matches:', '').strip()
            else:
                specialty_list = normalized
            return [s.strip() for s in specialty_list.split(',') if s.strip()]
        else:
            return [normalized] if normalized and not self.is_no_match(normalized) else []

    def is_multiple(self, specialty: str) -> bool:
        """Check if specialty string contains multiple specialties."""
        return len(self.extract_specialty_list(specialty)) > 1

    def is_no_match(self, specialty: str) -> bool:
        """Check if specialty string means no match."""
        return not specialty or specialty.lower() in {"no specialty match", "aucune correspondance", "no match", ""}

    def get_primary_specialty(self, specialty: str) -> Optional[str]:
        """Get the primary specialty (first in list for multiple matches)."""
        lst = self.extract_specialty_list(specialty)
        return lst[0] if lst else None

    def calculate_confidence(self, specialty: str, detection_method: str) -> float:
        """Calculate confidence level based on detection method and result."""
        if self.is_no_match(specialty):
            return 0.0
        if detection_method == "keyword":
            return 0.9 if not self.is_multiple(specialty) else 0.8
        elif detection_method == "llm":
            return 0.7 if not self.is_multiple(specialty) else 0.6
        else:
            return 0.5

    
    # def format_specialty_for_display(self, specialty: str) -> str:
    #     """Format specialty for user display."""
    #     normalized = self.normalize_specialty_format(specialty)
    #     if self.is_no_match(normalized):
    #         return "Aucune spécialité détectée"
    #     if normalized.startswith("multiple matches:"):
    #         return f"Plusieurs spécialités détectées: {normalized.replace('multiple matches:', '').strip()}"
    #     return normalized
    
    # def get_specialty_suggestions(self, partial_specialty: str) -> List[str]:
    #     """Return up to 10 specialty suggestions for partial input."""
    #     if not partial_specialty:
    #         return []
    #     partial_lower = partial_specialty.lower()
    #     suggestions = [s for s in self.specialty_list if partial_lower in s.lower()]
    #     for cat, specs in self.specialty_categories_dict.items():
    #         if partial_lower in cat.lower():
    #             suggestions.extend(specs)
    #         else:
    #             suggestions.extend([s for s in specs if partial_lower in s.lower()])
    #     return list(dict.fromkeys(suggestions))[:10]
    
    def get_specialty_category(self, specialty: str) -> Optional[str]:
        """Return category for a specialty, or None."""
        return next((cat for cat, specs in self.specialty_categories_dict.items() if specialty in specs), None)
    
    def is_specialty_valid(self, specialty: str) -> bool:
        if not specialty:
            return False
        if specialty in self.specialty_list:
            return True
        for specs in self.specialty_categories_dict.values():
            if specialty in specs:
                return True
        return False