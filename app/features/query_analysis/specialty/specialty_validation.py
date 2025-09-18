""" 
specialty_validation.py
---------------------------------
This module provides functionality to validate and map medical specialties
using fuzzy matching techniques.
"""

import pandas as pd
import re 
from typing import List
import unidecode
from app.config.features_config import ERROR_MESSAGES
from app.config.file_paths_config import PATHS
from app.utility.specialty_dicts_lists import specialty_categories_dict as default_dict, category_variations


class SpecialtyValidatorCheckException(Exception):
    pass


class SpecialtyValidator:
    """
    Class to validate and map medical specialties using fuzzy matching. 
    It uses a predefined list of specialties and categories to perform the matching.    
    Attributes:
        specialty_list (List[str]): List of canonical specialties.
        specialty_categories_dict (dict): Dictionary mapping categories to sub-specialties.
        key_words (str): Formatted string of specialty-keyword mappings for LLM prompts.    
    Methods:
        validate_specialty(raw_specialty: str or List[str]) -> List[str]:
            Validates and maps the input specialty string or list to canonical specialties. Returns a list of matched specialties or raises an exception if no match is found.  
        _map_llm_output_to_specialties(llm_output: str) -> dict:
            Internal method to map raw LLM output to specialties using fuzzy matching logic.  
        _fuzzy_match_any(text: str) -> str:
            Internal method to perform permissive fuzzy matching against specialties and categories.    
    """
    def __init__(self, specialty_list: List[str], specialty_categories_dict=None):
        # Normalize specialty list: lowercase, no accents, strip
        self.specialty_list = [unidecode.unidecode(s).lower().strip() for s in self._load_specialty_list_from_excel(PATHS["ranking_file_path"])]
        self.specialty_categories_dict = specialty_categories_dict or default_dict
        self.key_words = self._build_default_key_words(PATHS["mapping_word_path"])


    def _load_specialty_list_from_excel(self, path: str, sheet_name: str = "Palmarès") -> List[str]:
        import pandas as pd
        try:
            df_specialty = pd.read_excel(path, sheet_name=sheet_name)
            return df_specialty.iloc[:, 0].drop_duplicates().dropna().tolist()
        except Exception:
            all_specialties = []
            for specialties in default_dict.values():
                all_specialties.extend(specialties)
            return list(set(all_specialties))


    def _build_default_key_words(self, mapping_word_path: str) -> str:
        try:
            df = pd.read_csv(mapping_word_path)
            mapping_lines = []
            for _, row in df.iterrows():
                specialty = str(row["Valeurs"]).strip()
                keywords = str(row["Réponse LLM"]).strip()
                if ":" in keywords:
                    keywords = keywords.split(":", 1)[-1].strip()
                keywords = keywords.strip(" .;")
                if keywords:
                    mapping_lines.append(f"{specialty}: {keywords}")
                else:
                    mapping_lines.append(f"{specialty}:")
            return "\n".join(mapping_lines)
        except Exception as e:
            return "\n".join(f"{cat}: {', '.join(specialties)}" for cat, specialties in specialty_categories_dict.items())
        

    def _is_no_match(self, specialty: str) -> bool:
        """Check if specialty string means no match."""
        return not specialty or specialty.lower() in {"no specialty match", "aucune correspondance", "no match", ""}
    

    def _normalize(self, s):
        if not s:
            return ""
        s = unidecode.unidecode(s.lower())
        # Remove common French articles/prepositions
        s = re.sub(r"\b(du|de la|de l'|de|la|le|les|au|aux|a la|a l'|a|des|pour|sur|concernant|au niveau du|au niveau de|au niveau des|question|la|le|les)\b", "", s)
        s = re.sub(r"[^a-z0-9 ]", " ", s)  # Remove punctuation
        s = re.sub(r"\s+", " ", s).strip()
        return s


    def _fuzzy_match_any(self, text: str) -> str:
        """
        Fuzzy match input text to canonical specialties, sub-specialties, and category variations using substring matching.
        Returns the first match found, or a 'multiple matches:' string if a category variation matches, else None.
        """
        norm_text = self._normalize(text)
        # 1. Check specialty list (substring match)
        for specialty in self.specialty_list:
            if self._normalize(specialty) in norm_text:
                return specialty
        # 2. Check specialty_categories_dict (sub-specialties, substring match)
        for category, keywords in self.specialty_categories_dict.items():
            for keyword in keywords:
                if self._normalize(keyword) in norm_text:
                    return keyword
        # 3. Check category_variations (substring match)
        for category, variations in category_variations.items():
            for variation in variations:
                if self._normalize(variation) in norm_text:
                    return "multiple matches:" + ",".join(self.specialty_categories_dict.get(category.title(), []))
        return None


    def _map_llm_output_to_specialties(self, llm_output: str) -> dict:
        """
        Given the raw LLM output (comma-separated or string),
        normalize and map to canonical specialties, categories, or variations using permissive fuzzy matching.
        Implements the following logic:
        1. Count the number of detected specialties.
           a. If more than one, return the list for user selection.
           b. If only one, continue.
        2. Fuzzy match (permissive) against canonical specialties, sub-specialties, and category variations.
           a. If found, return as final detected specialty or category specialties for user selection.
           b. If not found, raise exception with error message.
        """
        if not llm_output or self._is_no_match(llm_output):
            raise SpecialtyValidatorCheckException(ERROR_MESSAGES["specialty_not_found"])
        # Split and normalize
        if isinstance(llm_output, str):
            candidates = [s.strip() for s in re.split(r'[;\,\n]', llm_output) if s.strip()]
        elif isinstance(llm_output, list):
            candidates = [str(s).strip() for s in llm_output if str(s).strip()]
        else:
            candidates = []
        if len(candidates) > 1:
            return {"multiple_specialties": sorted(set(candidates))}
        elif len(candidates) == 1:
            specialty = candidates[0]
            # Fuzzy match any (permissive)
            match = self._fuzzy_match_any(specialty)
            if match:
                if match.startswith("multiple matches:"):
                    # Return associated values for user selection
                    specialties = match.replace("multiple matches:", "").strip()
                    specialties_list = [s.strip() for s in specialties.split(',') if s.strip()]
                    return {"multiple_specialties": specialties_list}
                else:
                    return {"specialty": match}
            # No match
            raise SpecialtyValidatorCheckException(ERROR_MESSAGES["specialty_not_found"])
        else:
            raise SpecialtyValidatorCheckException(ERROR_MESSAGES["specialty_not_found"])


    def validate_specialty(self, raw_specialty) -> List[str]:
        """
        Utility interface: Accepts a string or list, delegates to map_llm_output_to_specialties, returns a list of specialties (if any).
        """
        if isinstance(raw_specialty, list):
            input_str = ', '.join([str(s) for s in raw_specialty if s])
        else:
            input_str = str(raw_specialty)
        result = self._map_llm_output_to_specialties(input_str)
        if 'specialty' in result:
            return [result['specialty']]
        elif 'multiple_specialties' in result:
            return result['multiple_specialties']
        else:
            return []

