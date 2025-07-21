"""
Module for detecting medical specialties mentioned in user queries.
"""
import pandas as pd
from app.config.file_paths_config import PATHS
from typing import Optional, List, Dict, Union
from enum import Enum
from app.utility.logging import get_logger
from app.utility.llm_helpers import invoke_llm_with_error_handling
from app.utility.wrappers import parse_llm_response, SpecialtyResponse
from app.utility.wrappers import prompt_formatting
from app.utility.specialty_dicts_lists import specialty_categories_dict, category_variations, general_cancer_terms


logger = get_logger(__name__)

class SpecialtyDetectionResult:
    """
    Container for specialty detection results.
    
    Attributes:
        specialty: The detected specialty string
        specialty_list: List of individual specialties (for multiple matches)
        detection_method: Method used for detection ('keyword' or 'llm')
        is_multiple: Whether multiple specialties were detected
        is_no_match: Whether no specialty was detected
        confidence: Confidence level of the detection
    """
    
    def __init__(self, specialty: str, detection_method: str = "unknown"):
        self.specialty = specialty
        self.detection_method = detection_method
        self.specialty_list = self._extract_specialty_list(specialty)
        self.is_multiple = self._is_multiple_specialty()
        self.is_no_match = self._is_no_specialty_match()
        self.confidence = self._calculate_confidence()
    
    def _extract_specialty_list(self, specialty: str) -> List[str]:
        """Extract list of individual specialties from formatted specialty string."""
        if not specialty:
            return []
        
        # Handle multiple specialties
        if ',' in specialty or specialty.startswith(('multiple matches:', 'plusieurs correspondances:')):
            if specialty.startswith(('multiple matches:', 'plusieurs correspondances:')):
                specialty_list = specialty.replace('multiple matches:', '').replace('plusieurs correspondances:', '').strip()
            else:
                specialty_list = specialty
            
            # Split by comma and clean each specialty
            return [s.strip() for s in specialty_list.split(',') if s.strip()]
        else:
            # Single specialty
            return [specialty] if specialty and not self._is_no_specialty_match() else []
    
    def _is_multiple_specialty(self) -> bool:
        """Check if multiple specialties were detected."""
        return len(self.specialty_list) > 1
    
    def _is_no_specialty_match(self) -> bool:
        """True if specialty is empty or a known 'no match' string."""
        return not self.specialty or self.specialty.lower() in {"no specialty match", "aucune correspondance", "no match", ""}
    
    def _calculate_confidence(self) -> float:
        """Calculate confidence level based on detection method and result."""
        if self.is_no_match:
            return 0.0
        
        if self.detection_method == "keyword":
            return 0.9 if not self.is_multiple else 0.8
        elif self.detection_method == "llm":
            return 0.7 if not self.is_multiple else 0.6
        else:
            return 0.5
    
    def get_primary_specialty(self) -> Optional[str]:
        """Get the primary specialty (first in list for multiple matches)."""
        return self.specialty_list[0] if self.specialty_list else None
    
    def __str__(self) -> str:
        return f"SpecialtyDetectionResult(specialty='{self.specialty}', method={self.detection_method}, multiple={self.is_multiple})"


class SpecialtyDetector:
    """
    Comprehensive service for detecting medical specialties in user queries.
    
    This class handles all aspects of specialty detection:
    - Keyword-based detection for fast, accurate matching
    - LLM-based detection with conversation context
    - Multi-specialty detection and normalization
    - Cancer specialty handling (general vs specific)
    - Specialty validation and formatting
    
    Attributes:
        model: The language model used for detection
        specialty_list: List of valid specialty names
        specialty_categories_dict: Dictionary mapping categories to specialties
        key_words: Keyword mappings for specialty detection
        
    Methods:
        detect_specialty: Main method for detecting specialties
        detect_specialty_with_context: Detect specialty with conversation history
        detect_specialty_keyword_only: Keyword-based detection only
        detect_specialty_llm_only: LLM-based detection only
        detect_specialty_status: Detect specialty presence status
        validate_specialty: Validate if specialty exists in system
        normalize_specialty_format: Normalize specialty format
        get_specialty_category: Get category for a specific specialty
    """
    
    def __init__(self, model, key_words=None):
        self.model = model
        self.specialty_categories_dict = specialty_categories_dict
        self.category_variations = category_variations
        self.general_cancer_terms = general_cancer_terms
        self.specialty_list = self._load_specialty_list()
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
    
    def detect_general_cancer_query(self, message: str) -> bool:
        """True if message is about cancer in general, not a specific type."""
        msg = message.lower().strip()
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

    def detect_specialty(self, prompt: str, conv_history: str = "") -> SpecialtyDetectionResult:
        """
        Main method for detecting medical specialties from user queries.
        
        Uses a hybrid approach:
        1. First tries keyword-based detection for speed and accuracy
        2. Falls back to LLM-based detection if no keyword match
        3. Handles special cases like cancer detection
        
        Args:
            prompt (str): The user's query message
            conv_history (str, optional): Conversation history for context
            
        Returns:
            SpecialtyDetectionResult: Comprehensive detection result
        """
        logger.info(f"Detecting specialty from prompt: '{prompt[:50]}...'")
        
        # Step 1: Try keyword-based detection first
        keyword_result = self._detect_specialty_keywords(prompt)
        if keyword_result and not keyword_result.is_no_match:
            logger.info(f"Specialty detected via keywords: {keyword_result.specialty}")
            return keyword_result
        
        # Step 2: Fall back to LLM-based detection
        llm_result = self._detect_specialty_llm(prompt, conv_history)
        logger.info(f"Specialty detection result: {llm_result}")
        
        return llm_result
    
    def detect_specialty_with_context(self, prompt: str, conv_history: str = "", detected_specialty: str = None) -> SpecialtyDetectionResult:
        """Return context specialty if given, else detect."""
        if detected_specialty:
            logger.info(f"Using provided specialty from context: {detected_specialty}")
            return SpecialtyDetectionResult(detected_specialty, "context")
        return self.detect_specialty(prompt, conv_history)
    
    def detect_specialty_keyword_only(self, prompt: str) -> SpecialtyDetectionResult:
        """Keyword-only specialty detection."""
        return self._detect_specialty_keywords(prompt)
    
    def detect_specialty_llm_only(self, prompt: str, conv_history: str = "") -> SpecialtyDetectionResult:
        """LLM-only specialty detection."""
        return self._detect_specialty_llm(prompt, conv_history)
    
    def detect_specialty_status(self, prompt: str, conv_history: str = "") -> SpecialtyResponse:
        """
        Detect the status of specialty mention in the query.
        
        Args:
            prompt (str): The user's query message
            conv_history (str, optional): Conversation history for context
            
        Returns:
            SpecialtyResponse: Status of specialty detection
        """
        # Use a simple LLM call to determine status
        formatted_prompt = self._format_specialty_status_prompt(prompt, conv_history)
        raw_response = invoke_llm_with_error_handling(
            self.model, 
            formatted_prompt, 
            "detect_specialty_status"
        )
        
        return parse_llm_response(raw_response, "specialty")
    
    def validate_specialty(self, specialty: str) -> bool:
        """True if specialty is valid."""
        return bool(specialty) and (specialty in self.specialty_list or any(specialty in specs for specs in self.specialty_categories_dict.values()))
    
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
    
    def get_specialty_category(self, specialty: str) -> Optional[str]:
        """Return category for a specialty, or None."""
        return next((cat for cat, specs in self.specialty_categories_dict.items() if specialty in specs), None)
    
    def _detect_specialty_keywords(self, prompt: str) -> SpecialtyDetectionResult:
        """
        Internal method for keyword-based specialty detection.
        
        Args:
            prompt (str): The user's query message
            
        Returns:
            SpecialtyDetectionResult: Keyword-based detection result
        """
        # Use the existing keyword extraction function
        keyword_result = self.extract_specialty_keywords(prompt)
        
        if keyword_result:
            # Handle special case: general cancer query
            if keyword_result.startswith("multiple matches:") and self.detect_general_cancer_query(prompt):
                logger.info("General cancer query detected")
                return SpecialtyDetectionResult(keyword_result, "keyword")
            
            return SpecialtyDetectionResult(keyword_result, "keyword")
        
        return SpecialtyDetectionResult("no specialty match", "keyword")
    
    def _detect_specialty_llm(self, prompt: str, conv_history: str = "") -> SpecialtyDetectionResult:
        """
        Internal method for LLM-based specialty detection.
        
        Args:
            prompt (str): The user's query message
            conv_history (str, optional): Conversation history for context
            
        Returns:
            SpecialtyDetectionResult: LLM-based detection result
        """
        # Format the prompt for LLM
        formatted_prompt = prompt_formatting(
            "second_detect_specialty_prompt",
            mapping_words=self.key_words,
            prompt=prompt,
            conv_history=conv_history
        )
        
        # Call LLM
        raw_specialty = invoke_llm_with_error_handling(
            self.model, 
            formatted_prompt, 
            "detect_specialty_llm"
        )
        
        # Normalize the result
        normalized_specialty = self.normalize_specialty_format(raw_specialty)
        
        return SpecialtyDetectionResult(normalized_specialty, "llm")
    
    def _format_specialty_status_prompt(self, prompt: str, conv_history: str = "") -> str:
        """
        Format prompt for specialty status detection.
        
        Args:
            prompt (str): The user's query message
            conv_history (str, optional): Conversation history for context
            
        Returns:
            str: Formatted prompt for LLM
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
    
    @property
    def all_cancer_specialties(self) -> List[str]:
        """Get all cancer specialties (cached)."""
        if self._all_cancer_specialties is None:
            self._all_cancer_specialties = self.get_all_cancer_specialties()
        return self._all_cancer_specialties
    
    def is_cancer_specialty(self, specialty: str) -> bool:
        """Check if a specialty is cancer-related."""
        return specialty in self.all_cancer_specialties
    
    def detect_general_cancer_query(self, prompt: str) -> bool:
        """Check if the query is about cancer in general."""
        return self.detect_general_cancer_query(prompt)
    
    def get_cancer_specialties_for_query(self, prompt: str) -> List[str]:
        """Get cancer specialties relevant to the query."""
        if self.detect_general_cancer_query(prompt):
            return self.all_cancer_specialties
        return []
    
    def extract_specialty_list_from_result(self, result: SpecialtyDetectionResult) -> List[str]:
        """Extract specialty list from detection result."""
        return result.specialty_list
    
    def format_specialty_for_display(self, specialty: str) -> str:
        """Format specialty for user display."""
        if not specialty or specialty == "no specialty match":
            return "Aucune spécialité détectée"
        if specialty.startswith("multiple matches:"):
            return f"Plusieurs spécialités détectées: {specialty.replace('multiple matches:', '').strip()}"
        return specialty
    
    def get_specialty_suggestions(self, partial_specialty: str) -> List[str]:
        """Return up to 10 specialty suggestions for partial input."""
        if not partial_specialty:
            return []
        partial_lower = partial_specialty.lower()
        suggestions = [s for s in self.specialty_list if partial_lower in s.lower()]
        for cat, specs in self.specialty_categories_dict.items():
            if partial_lower in cat.lower():
                suggestions.extend(specs)
            else:
                suggestions.extend([s for s in specs if partial_lower in s.lower()])
        return list(dict.fromkeys(suggestions))[:10]
