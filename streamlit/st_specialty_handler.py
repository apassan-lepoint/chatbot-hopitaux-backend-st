"""
Handles specialty detection and selection logic for Streamlit UI.
"""

import streamlit as st
from datetime import datetime

from app.services.llm_handler_service import LLMHandler

from app.utility.logging import get_logger

from st_config import (
    SESSION_STATE_KEYS,
    UI_SPECIALTY_SELECTION_PROMPT,
    UI_INVALID_SELECTION_ERROR
)
from st_utility import get_session_state_value



logger = get_logger(__name__)



class SpecialtyHandler:
    """
    SpecialtyHandler manages specialty detection and selection in the Streamlit UI.
    It interacts with the LLMHandler to detect specialties from user prompts,
    normalizes specialty formats, and handles user selections when multiple specialties are detected.   
    
    Attributes:
        llm_handler (LLMHandler): Instance of LLMHandler to interact with the language model for specialty detection.       
        
    Methods:
        get_current_specialty_context() -> str: Retrieves the current specialty context from session state.
        normalize_specialty_format(specialty: str) -> str: Normalizes specialty format to use consistent prefix.
        extract_specialty_options(specialty: str) -> list: Extracts specialty options from formatted string.
        handle_specialty_selection(prompt: str, key_suffix: str = "") -> str:
            Handles specialty selection UI and logic, allowing user to select from multiple specialties.
        detect_and_handle_specialty(prompt: str) -> tuple:
            Detects specialty from user prompt and handles cases with multiple matches.    
    """
    
    def __init__(self, llm_handler: LLMHandler):
        self.llm_handler = llm_handler
    
    
    def get_current_specialty_context(self) -> str:
        """
        Retrieves the current specialty context from session state. 
        
        Args:
            None
            
        Returns:
            str: The currently selected specialty or None if no specialty is set.
        """
        selected_specialty = get_session_state_value(SESSION_STATE_KEYS["selected_specialty"], None)
        if selected_specialty:
            return selected_specialty
        
        specialty_context = get_session_state_value(SESSION_STATE_KEYS["specialty_context"], None)
        if specialty_context and specialty_context.get("selected_specialty"):
            return specialty_context["selected_specialty"]
        
        detected_specialty = get_session_state_value(SESSION_STATE_KEYS["specialty"], "")
        if detected_specialty and not detected_specialty.startswith(("multiple matches:", "plusieurs correspondances:")):
            return detected_specialty
        
        return None
    
    
    def normalize_specialty_format(self, specialty: str) -> str:
        """
        Normalize specialty format to use consistent prefix.
        
        Args:
            specialty: The specialty string to normalize
            
        Returns:
            str: Normalized specialty string with consistent prefix
        """
        if specialty.startswith("plusieurs correspondances:"):
            return specialty.replace("plusieurs correspondances:", "multiple matches:")
        return specialty
    
    
    def extract_specialty_options(self, specialty: str) -> list:
        """
        Extract specialty options from formatted string.
        
        Args:
            specialty: The specialty string containing multiple options 
            
        Returns:
            list: List of unique specialty options extracted from the string
        """
        if specialty.startswith("multiple matches:"):
            options_str = specialty.removeprefix("multiple matches:").strip()
        elif specialty.startswith("plusieurs correspondances:"):
            options_str = specialty.removeprefix("plusieurs correspondances:").strip()
        else:
            return []
        
        return list(dict.fromkeys([opt.strip() for opt in options_str.split(',') if opt.strip()]))
    
    
    def handle_specialty_selection(self, prompt: str, key_suffix: str = "") -> str:
        """
        Handle specialty selection UI and logic.
        
        Args:
            prompt: The user's prompt
            key_suffix: Suffix for radio button key to avoid conflicts
            
        Returns:
            Selected specialty if valid selection made, None otherwise
        """
        multiple_specialties = get_session_state_value(SESSION_STATE_KEYS["multiple_specialties"], None)
        if multiple_specialties is not None:
            selected_specialty = st.radio(
                UI_SPECIALTY_SELECTION_PROMPT, 
                multiple_specialties, 
                index=None,
                key=f"specialty_radio{key_suffix}"
            )
            
            if selected_specialty and selected_specialty in multiple_specialties:
                st.session_state.selected_specialty = selected_specialty
                st.session_state.specialty_context = {
                    'original_query': prompt,
                    'selected_specialty': selected_specialty,
                    'timestamp': datetime.now().isoformat()
                }
                st.session_state.multiple_specialties = None
                logger.info(f"User selected valid specialty: {selected_specialty}")
                return selected_specialty
            elif selected_specialty:
                st.error(UI_INVALID_SELECTION_ERROR)
        return None
    
    
    def detect_and_handle_specialty(self, prompt: str) -> tuple:
        """
        Detect specialty and handle multiple matches.
        
        Args:
            prompt: The user's prompt
            
        Returns:
            Tuple of (specialty, needs_rerun) where needs_rerun indicates if UI should rerun
        """
        specialty = get_session_state_value(SESSION_STATE_KEYS["specialty"], "")
        
        if specialty == "":
            detected_specialty = self.llm_handler.detect_specialty(prompt)
            specialty = self.normalize_specialty_format(detected_specialty)
            st.session_state.specialty = specialty

        if specialty.startswith("multiple matches:"):
            logger.info("Multiple specialties detected, prompting user for selection")
            options = self.extract_specialty_options(specialty)
            if options:
                st.session_state.multiple_specialties = options
                st.session_state.original_prompt = prompt
                return None, True  # Needs rerun
            else:
                # Fallback to no specialty if extraction fails
                return "aucune correspondance", False
        else:
            # Single specialty detected or no specialty
            if not specialty or specialty in ["no specialty match", "aucune correspondance", ""]:
                specialty = "no specialty match"
            return specialty, False