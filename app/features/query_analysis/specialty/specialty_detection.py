import pandas as pd
import unidecode
from app.config.file_paths_config import PATHS
from typing import Optional, List, Tuple
from app.utility.logging import get_logger
from app.utility.llm_helpers import invoke_llm_with_error_handling
from app.utility.wrappers import parse_llm_response, prompt_formatting
from app.utility.specialty_dicts_lists import specialty_categories_dict, category_variations, general_cancer_terms


logger = get_logger(__name__)


class SpecialtyDetector:
    """
    Only detects specialty string and detection method.
    """
    def __init__(self, model, key_words=None):
        self.model = model
        self.specialty_categories_dict = specialty_categories_dict
        self.category_variations = category_variations
        self.general_cancer_terms = general_cancer_terms
        # Normalize specialty list: lowercase, no accents, strip
        self.specialty_list = [unidecode.unidecode(s).lower().strip() for s in self._load_specialty_list()]
        self.key_words = key_words or self._build_default_key_words()
        self._all_cancer_specialties = None

    def _load_specialty_list(self):
        try:
            df_specialty = pd.read_excel(PATHS["ranking_file_path"], sheet_name="Palmarès")
            return df_specialty.iloc[:, 0].drop_duplicates().dropna().tolist()
        except Exception:
            all_specialties = []
            for specialties in self.specialty_categories_dict.values():
                all_specialties.extend(specialties)
            return list(set(all_specialties))

    def _build_default_key_words(self) -> str:
        """Build default keyword mappings from specialty categories."""
        return "\n".join(f"{cat}: {', '.join(specialties)}" for cat, specialties in self.specialty_categories_dict.items())


    def _detect_specialty_keywords(self, prompt: str) -> Tuple[str, str]:
        """
        Returns (specialty_string, method)
        """
        keyword_result = self.extract_specialty_keywords(prompt)
        if keyword_result:
            if keyword_result.startswith("multiple matches:") and self.detect_general_cancer_query(prompt):
                logger.info("General cancer query detected")
                return keyword_result, "keyword"
            return keyword_result, "keyword"
        return "no specialty match", "keyword"
    
    def _detect_specialty_llm(self, prompt: str, conv_history: str = "") -> Tuple[str, str]:
        """
        Returns (specialty_string, method)
        """
        formatted_prompt = prompt_formatting(
            "second_detect_specialty_prompt",
            mapping_words=self.key_words,
            prompt=prompt,
            conv_history=conv_history
        )
        raw_specialty = invoke_llm_with_error_handling(
            self.model, 
            formatted_prompt, 
            "detect_specialty_llm"
        )
        return raw_specialty, "llm"
    
    def _format_specialty_status_prompt(self, prompt: str, conv_history: str = "") -> str:
        """

        """
        formatted_history = f"Historique de la conversation:\n{conv_history}\n\n" if conv_history.strip() else ""
        
        return f"""
{formatted_history}Voici une liste de spécialité pour laquelle tu vas devoir choisir la spécialité qui correspond le plus à mon message : 
liste des spécialités: '{self.specialty_list}'. 

Analysez le message de l'utilisateur et déterminez si une ou plusieurs spécialités médicales dans la liste des spécialités sont mentionnées:
0 - Aucune spécialité médicale mentionnée
1 - Une spécialité médicale mentionnée
2 - Plusieurs spécialités médicales mentionnées

MESSAGE À ANALYSER: '{prompt}'
"""
    
    def get_all_cancer_specialties(self):
        """Return all cancer specialties, excluding surgical ones."""
        if self._all_cancer_specialties is not None:
            return self._all_cancer_specialties
        excluded_terms = {"chirurgie", "surgery", "surgical"}
        self._all_cancer_specialties = [
            s for specialties in self.specialty_categories_dict.values() for s in specialties
            if "cancer" in s.lower() and not any(term in s.lower() for term in excluded_terms)
        ]
        return self._all_cancer_specialties
    
    def detect_general_cancer_query(self, prompt: str) -> bool:
        """Check if the query is about cancer in general."""
        msg = prompt.lower().strip()
        if any(term in msg for term in self.general_cancer_terms):
            if not any(s.lower() in msg for s in self.get_all_cancer_specialties()):
                return True
        return False
    
    def extract_specialty_keywords(self, message: str) -> str:
        """Return detected specialty or multiple matches string."""
        msg = message.lower()
        if self.detect_general_cancer_query(msg):
            return "multiple matches:" + ",".join(self.get_all_cancer_specialties())
        for category, keywords in self.specialty_categories_dict.items():
            for keyword in keywords:
                if keyword.lower() in msg and (len(keyword.split()) > 1 or keyword.lower() == msg.strip()):
                    return keyword
            cat_lower = category.lower()
            if cat_lower in msg:
                return "multiple matches:" + ",".join(keywords)
            if cat_lower in self.category_variations:
                for variation in self.category_variations[cat_lower]:
                    if len(variation.split()) == 1:
                        import re
                        if re.search(rf'\b{re.escape(variation)}\b', msg, re.IGNORECASE):
                            return "multiple matches:" + ",".join(keywords)
                    elif variation in msg:
                        return "multiple matches:" + ",".join(keywords)
        return None
    
    def detect_specialty(self, prompt: str, conv_history: str = "") -> Tuple[str, str]:
        """
        Returns a tuple: (raw_specialty_string, detection_method)
        Always unpack the result as:
            specialty, method = detector.detect_specialty(...)
        Never use .specialty on the result, as it is a tuple.
        """
        logger.info(f"Detecting specialty from prompt: '{prompt}'")
        # Step 1: Try keyword-based detection first
        specialty, method = self._detect_specialty_keywords(prompt)
        if specialty and specialty.lower() not in {"no specialty match", "aucune correspondance", "no match", ""}:
            logger.info(f"Specialty detected via keywords: {specialty}")
            return specialty, method
        # Step 2: Fall back to LLM-based detection
        specialty, method = self._detect_specialty_llm(prompt, conv_history)
        logger.info(f"Specialty detection result: {specialty}, method: {method}")
        return specialty, method
    
    
    def detect_specialty_keyword_only(self, prompt: str) -> Tuple[str, str]:
        """Keyword-only specialty detection."""
        return self._detect_specialty_keywords(prompt)
    
    def detect_specialty_llm_only(self, prompt: str, conv_history: str = "") -> Tuple[str, str]:
        """LLM-only specialty detection."""
        return self._detect_specialty_llm(prompt, conv_history)
    
    
    @property
    def all_cancer_specialties(self) -> List[str]:
        """Get all cancer specialties (cached)."""
        if self._all_cancer_specialties is None:
            self._all_cancer_specialties = self.get_all_cancer_specialties()
        return self._all_cancer_specialties
    
    def is_cancer_specialty(self, specialty: str) -> bool:
        """Check if a specialty is cancer-related."""
        return specialty in self.all_cancer_specialties
    
    def get_cancer_specialties_for_query(self, prompt: str) -> List[str]:
        """Get cancer specialties relevant to the query."""
        if self.detect_general_cancer_query(prompt):
            return self.all_cancer_specialties
        return []
