"""
Handles specialty detection and selection logic for Streamlit UI.
"""

import streamlit as st
from datetime import datetime
from app.utility.logging import get_logger
from app.features.query_analysis.specialty.specialty_detection import SpecialtyDetector
from st_config import (SESSION_STATE_KEYS, UI_SPECIALTY_SELECTION_PROMPT, UI_INVALID_SELECTION_ERROR, NO_SPECIALTY_MATCH)
from st_utility import get_session_state_value

# Initialize logger for this module
logger = get_logger(__name__)

class SpecialtyHandler:
    """
    SpecialtyHandler class for managing specialty detection and selection in Streamlit UI.
    Uses a backend LLMHandler for specialty detection and manages session state
    for user-selected specialties.
    Attributes:
        llm_handler (LLMHandler): Backend service for specialty detection.
        specialty_detector (SpecialtyDetector): Instance for detecting specialties.
    Methods:
        get_current_specialty_context: Retrieves the current specialty context from session state.
        normalize_specialty_format: Normalizes specialty format to use consistent prefix for multiple matches.
        extract_specialty_options: Extracts specialty options from a formatted string containing multiple matches.
        handle_specialty_selection: Handles specialty selection UI and logic for multiple detected specialties.
        detect_and_handle_specialty: Detects specialty from user prompt and handles cases with multiple matches
    """
    def __init__(self, llm_handler):
        logger.info("Initializing SpecialtyHandler")
        self.llm_handler = llm_handler
        # Use SpecialtyDetector for specialty detection
        self.specialty_detector = SpecialtyDetector(llm_handler.model)


    def get_current_specialty_context(self) -> str:
        """
        The function to get the current specialty context.  
        It checks session state for selected specialty, existing specialty context,
        or detected specialty, returning the appropriate value. 

        Args:
            None        
        Returns:
            str: The current specialty context or None if not found.    
        """
        logger.debug("Getting current specialty context")

        # Check if a specialty has been selected by the user
        selected_specialty = get_session_state_value(SESSION_STATE_KEYS["selected_specialty"], None)
        if selected_specialty:
            return selected_specialty

        # Check if specialty context exists in session state
        specialty_context = get_session_state_value(SESSION_STATE_KEYS["specialty_context"], None)
        if specialty_context and specialty_context.get("selected_specialty"):
            return specialty_context["selected_specialty"]

        # Check if a specialty was detected (not a multiple match string)
        detected_specialty = get_session_state_value(SESSION_STATE_KEYS["specialty"], "")
        if detected_specialty and not detected_specialty.startswith(("multiple matches:", "plusieurs correspondances:")):
            return detected_specialty

        # No specialty found
        return None
    
    
    def normalize_specialty_format(self, specialty: str) -> str:
        logger.debug(f"Normalizing specialty format: {specialty}")
        """
        The method aims to normalize the format of a specialty string.
        It replaces the French prefix for multiple matches with the English equivalent. 

        Args:
            specialty (str): The specialty string to normalize. 
        Returns:
            str: The normalized specialty string with consistent prefix for multiple matches.
        """
        if specialty.startswith("plusieurs correspondances:"):
            return specialty.replace("plusieurs correspondances:", "multiple matches:")
        return specialty
    
    
    def extract_specialty_options(self, specialty: str) -> list:
        logger.debug(f"Extracting specialty options from: {specialty}")
        """
        The method extracts specialty options from a formatted string containing multiple matches.
        It handles both English and French prefixes for multiple matches, splits the options by comma,
        removes duplicates, and strips whitespace.  

        Args:
            specialty (str): The specialty string containing multiple matches.
        Returns:
            list: A list of unique specialty options extracted from the string. 
        """
        # Handle both English and French multiple match prefixes
        if specialty.startswith("multiple matches:"):
            options_str = specialty.removeprefix("multiple matches:").strip()
        elif specialty.startswith("plusieurs correspondances:"):
            options_str = specialty.removeprefix("plusieurs correspondances:").strip()
        else:
            return []
        # Split by comma, remove duplicates, and strip whitespace
        return list(dict.fromkeys([opt.strip() for opt in options_str.split(',') if opt.strip()]))
    
    
    def handle_specialty_selection(self, prompt: str, key_suffix: str = "") -> str:
        """
        The method handles the UI for selecting a specialty when multiple specialties are detected.
        It retrieves the list of specialties from session state, displays a radio button for selection,
        and updates session state with the selected specialty. If no valid selection is made, it shows an error.

        Args:      
            prompt (str): The user's prompt to provide context for specialty selection.
            key_suffix (str): Optional suffix for the Streamlit key to avoid conflicts in session state.    
        Returns:
            str: The selected specialty if a valid selection is made, otherwise None.   
        """
        # Get list of multiple specialties from session state
        multiple_specialties = get_session_state_value(SESSION_STATE_KEYS["multiple_specialties"], None)
        if multiple_specialties is not None:
            # Display radio button for user to select specialty
            selected_specialty = st.radio(
                UI_SPECIALTY_SELECTION_PROMPT, 
                multiple_specialties, 
                index=None,
                key=f"specialty_radio{key_suffix}"
            )

            # If user made a valid selection, update session state
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
            # If selection is invalid, show error
            elif selected_specialty:
                st.error(UI_INVALID_SELECTION_ERROR)
        # No selection made
        return None
    
    
    def detect_and_handle_specialty(self, prompt: str) -> tuple:
        """
        Detect specialty from user prompt and handle cases with multiple matches.
        Updates session state and determines if UI needs to rerun for user selection.

        Args:
            prompt: The user's prompt

        Returns:
            Tuple of (specialty, needs_rerun) where needs_rerun indicates if UI should rerun
        """
        # Get current specialty from session state
        specialty = get_session_state_value(SESSION_STATE_KEYS["specialty"], "")

        # If no specialty detected yet, use SpecialtyDetector to detect
        if specialty == "":
            detected_specialty_result = self.specialty_detector.detect_specialty(prompt)
            detected_specialty = detected_specialty_result.specialty
            specialty = self.normalize_specialty_format(detected_specialty)
            st.session_state.specialty = specialty

        # If multiple specialties detected, prompt user for selection
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
            if not specialty or specialty in [NO_SPECIALTY_MATCH, "aucune correspondance", ""]:
                specialty = NO_SPECIALTY_MATCH
            return specialty, False