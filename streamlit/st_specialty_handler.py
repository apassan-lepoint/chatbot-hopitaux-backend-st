"""
Handles specialty detection and selection logic for Streamlit UI.

This module provides the SpecialtyHandler class, which manages specialty detection,
normalization, and user selection in the Streamlit frontend. It bridges backend specialty
detection with frontend user interaction, updating session state and handling UI elements.
"""

import streamlit as st
from datetime import datetime
from app.utility.logging import get_logger
from streamlit.st_config import (
    SESSION_STATE_KEYS,
    UI_SPECIALTY_SELECTION_PROMPT,
    UI_INVALID_SELECTION_ERROR
)
from streamlit.st_utility import get_session_state_value

logger = get_logger(__name__)

class SpecialtyHandler:
    """
    Manages specialty detection and selection in the Streamlit UI.
    - Interacts with LLMHandler to detect specialties from user prompts.
    - Normalizes specialty formats for consistent handling.
    - Handles user selection when multiple specialties are detected.
    """

    def __init__(self, llm_handler):
        """
        Initialize the SpecialtyHandler with a backend LLMHandler instance.
        Args:
            llm_handler (LLMHandler): Backend service for specialty detection.
        """
        self.llm_handler = llm_handler

    def get_current_specialty_context(self) -> str:
        """
        Retrieves the current specialty context from session state.
        Checks for selected specialty in session state, then specialty context,
        then detected specialty, and returns the first valid value found.

        Returns:
            str: The currently selected specialty or None if no specialty is set.
        """
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
        """
        Normalize specialty format to use consistent prefix for multiple matches.

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
        Extract specialty options from a formatted string containing multiple matches.
        Removes duplicates and trims whitespace.

        Args:
            specialty: The specialty string containing multiple options 

        Returns:
            list: List of unique specialty options extracted from the string
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
        Handle specialty selection UI and logic for multiple detected specialties.
        Displays a radio button for user selection and updates session state.

        Args:
            prompt: The user's prompt
            key_suffix: Suffix for radio button key to avoid conflicts

        Returns:
            Selected specialty if valid selection made, None otherwise
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

        # If no specialty detected yet, use LLMHandler to detect
        if specialty == "":
            detected_specialty = self.llm_handler.detect_specialty(prompt)
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
            if not specialty or specialty in ["no specialty match", "aucune correspondance", ""]:
                specialty = "no specialty match"
            return specialty, False