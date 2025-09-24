""" 
specialty_validation.py
---------------------------------
This module provides functionality to validate and map medical specialties
using fuzzy matching techniques.
"""

import difflib
import pandas as pd
import re 
import spacy
from typing import List
import unidecode
from app.config.features_config import ERROR_MESSAGES
from app.config.file_paths_config import PATHS
from app.utility.dicts_lists.specialty_dicts_lists import specialty_categories_dict, category_variations, specialty_list, generic_words
from app.utility.functions.formatting_helpers import normalize_text
from app.utility.functions.logging import get_logger

logger = get_logger(__name__)

class SpecialtyValidatorCheckException(Exception):
    pass


class SpecialtyValidator:
    """
    Class to validate and map medical specialties using fuzzy matching. 
    It uses a predefined list of specialties and categories to perform the matching.    
    Attributes:
    - specialty_list: List of canonical specialties.
    - specialty_categories_dict: Dict mapping categories to lists of specialties.
    - key_words: Pre-built string mapping specialties to keywords for LLM prompts.  
    Methods:
    - validate_specialty: Main interface to validate and map specialties.       
    - _map_llm_output_to_specialties: Core logic to map LLM output to specialties.
    - _fuzzy_match_any: Permissive fuzzy matching against specialties and categories.
    - _is_no_match: Check if specialty string indicates no match.
    - _build_default_key_words: Build default keywords mapping from CSV or fallback.
    """
    def __init__(self):
        # Normalize specialty list: lowercase, no accents, strip
        self.specialty_list = specialty_list
        self.specialty_categories_dict = specialty_categories_dict
        self.key_words = self._build_default_key_words(PATHS["mapping_word_path"])


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
    

    def _remove_generic_words(self, text: str) -> str:
        """
        Remove generic French medical words/phrases (with fuzzy matching for minor typos) from the input string.
        """
        # Tokenize by space and also check for multi-word phrases
        words = text.split()
        # Remove exact and fuzzy matches (threshold 0.85)
        filtered_words = []
        for i, word in enumerate(words):
            # Check for multi-word phrases (up to 3 words)
            found = False
            for n in [3,2,1]:
                if i + n <= len(words):
                    phrase = " ".join(words[i:i+n]).lower()
                    # Fuzzy match against generic_words
                    matches = difflib.get_close_matches(phrase, generic_words, n=1, cutoff=0.85)
                    if matches:
                        found = True
                        break
            if not found:
                filtered_words.append(word)
        return " ".join(filtered_words)

    def _lemmatize_french(self, text: str) -> str:
        """
        Lemmatize French text using spaCy (fr_core_news_sm). Returns the lemmatized string.
        """
        try:
            nlp = spacy.load("fr_core_news_sm")
            doc = nlp(text)
            return " ".join([token.lemma_ for token in doc])
        except Exception as e:
            logger.warning(f"spaCy lemmatization failed: {e}")
            return text

    def _fuzzy_match_any(self, text: str) -> str:
        """
        Fuzzy match input text to canonical specialties, sub-specialties, and category variations using substring matching and difflib similarity.
        Returns the first match found, or a 'multiple matches:' string if a category variation matches, else None.
        """
        import difflib
        # Remove generic words before matching
        text = self._remove_generic_words(text)
        # Lemmatize before matching
        text = self._lemmatize_french(text)
        norm_text = normalize_text(text)
        logger.debug(f"Normalized text for fuzzy matching: {norm_text}")

        # 3. Check category_variations (bidirectional substring match)
        for category in category_variations.keys():
            norm_category = normalize_text(category)
            ratio = difflib.SequenceMatcher(None, norm_text, norm_category).ratio()
            if ratio >= 0.8:
                logger.debug(f"Fuzzy match found to category key '{category}' (ratio={ratio})")
                return "multiple matches:" + ",".join(self.specialty_categories_dict.get(category, []))
            
        # 1. Check specialty list (bidirectional substring match)
        for specialty in self.specialty_list:
            norm_specialty = normalize_text(specialty)
            if norm_specialty in norm_text or norm_text in norm_specialty:
                logger.debug(f"Fuzzy match found in specialty list: {specialty}")
                return specialty
        # 2. Check specialty_categories_dict (sub-specialties, bidirectional substring match)
        for category, keywords in self.specialty_categories_dict.items():
            for keyword in keywords:
                norm_keyword = normalize_text(keyword)
                if norm_keyword in norm_text or norm_text in norm_keyword:
                    logger.debug(f"Fuzzy match found in category '{category}': {keyword}")
                    return keyword
        
            
        for category, variations in category_variations.items():
            for variation in variations:
                norm_variation = normalize_text(variation)
                if norm_variation in norm_text or norm_text in norm_variation:
                    logger.debug(f"Fuzzy match found in category variations '{category}': {variation}")
                    return "multiple matches:" + ",".join(self.specialty_categories_dict.get(category.title(), []))
        
        # 4. Fuzzy match using difflib for specialty_list
        best_match = None
        best_ratio = 0.0
        for specialty in self.specialty_list:
            norm_specialty = normalize_text(specialty)
            ratio = difflib.SequenceMatcher(None, norm_text, norm_specialty).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = specialty
        if best_ratio >= 0.8:
            logger.debug(f"difflib fuzzy match found in specialty list: {best_match} (ratio={best_ratio})")
            return best_match
        # 5. Fuzzy match using difflib for specialty_categories_dict
        for category, keywords in self.specialty_categories_dict.items():
            for keyword in keywords:
                norm_keyword = normalize_text(keyword)
                ratio = difflib.SequenceMatcher(None, norm_text, norm_keyword).ratio()
                if ratio >= 0.8:
                    logger.debug(f"difflib fuzzy match found in category '{category}': {keyword} (ratio={ratio})")
                    return keyword
        # 6. Fuzzy match using difflib for category_variations
        for category, variations in category_variations.items():
            for variation in variations:
                norm_variation = normalize_text(variation)
                ratio = difflib.SequenceMatcher(None, norm_text, norm_variation).ratio()
                if ratio >= 0.8:
                    logger.debug(f"difflib fuzzy match found in category variations '{category}': {variation} (ratio={ratio})")
                    return "multiple matches:" + ",".join(self.specialty_categories_dict.get(category.title(), []))
        logger.debug("No fuzzy match found")
        return None


    def _map_llm_output_to_specialties(self, llm_output: str) -> dict:
        """
        Given the raw LLM output (comma-separated or string),
        normalize and map to canonical specialties, categories, or variations using permissive fuzzy matching.
        Implements the following logic:
        1. If no specialty detected, continue (return empty).
        2. If specialty detected but fuzzy match fails, raise error.
        """
        # If no specialty detected, continue (return empty)
        if not llm_output or self._is_no_match(llm_output):
            return {"specialty": None}
        
        # Split and normalize
        if isinstance(llm_output, str):
            candidates = [s.strip() for s in re.split(r'[;\,\n]', llm_output) if s.strip()]
        elif isinstance(llm_output, list):
            candidates = [str(s).strip() for s in llm_output if str(s).strip()]
        else:
            candidates = []

        # If multiple specialties, return list    
        if len(candidates) > 1:
            return {
                "multiple_specialties": sorted(set(candidates)),
                "message": "Plusieurs spécialités correspondent à votre requête : " + ", ".join(sorted(set(candidates)))
            }
        # If single specialty, fuzzy match
        elif len(candidates) == 1:
            specialty = candidates[0]
            logger.debug(f"Fuzzy matching specialty: {specialty}")
            match = self._fuzzy_match_any(specialty)
            logger.debug(f"Fuzzy match result: {match}")
            if match:
                if match.startswith("multiple matches:"):
                    # Return associated values for user selection
                    specialties = match.replace("multiple matches:", "").strip()
                    specialties_list = [s.strip() for s in specialties.split(',') if s.strip()]
                    return {
                        "multiple_specialties": specialties_list,
                        "message": "Plusieurs spécialités correspondent à votre requête : " + ", ".join(specialties_list)
                    }
                else:
                    return {"specialty": match}
            # No match
            raise SpecialtyValidatorCheckException(ERROR_MESSAGES["specialty_not_found"])
        else:
            return {"specialty": None}


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
            return ['tableau d\'honneur']
