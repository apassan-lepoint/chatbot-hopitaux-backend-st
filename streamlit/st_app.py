"""
Main Streamlit-based user interface for the hospital ranking chatbot.
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st

from app.features.checks.sanity_sanity_checks_manager import SanityChecksManager

from app.utility.logging import get_logger
from app.utility.formatting_helpers import format_links

from streamlit.st_config import (
    DEFAULT_CHECKS_TO_RUN,
    SESSION_STATE_KEYS,
    MAX_MESSAGES,
    UI_CHAT_INPUT_PLACEHOLDER,
    ERROR_MESSAGES, 
    SPINNER_MESSAGES
)

from streamlit.st_utility import (
    append_to_conversation,
    display_conversation_history,
    get_conversation_list,
    get_conversation_length,
    get_session_state_value,
    execute_with_spinner
)
from streamlit.st_specialty_handler import SpecialtyHandler
from streamlit.st_message_handler import MessageHandler
from streamlit.st_ui_components import UIComponents


logger = get_logger(__name__)


class StreamlitChatbot:
    """
    Main Streamlit chatbot UI class.
    This class encapsulates the entire chatbot functionality, including UI setup,
    message handling, and session state management.
    """

    SESSION_STATE_DEFAULTS = {
        SESSION_STATE_KEYS["conversation"]: [],
        SESSION_STATE_KEYS["selected_option"]: None,
        SESSION_STATE_KEYS["prompt"]: "",
        SESSION_STATE_KEYS["specialty"]: "",
        SESSION_STATE_KEYS["selected_specialty"]: None,
        SESSION_STATE_KEYS["specialty_context"]: None,
        SESSION_STATE_KEYS["multiple_specialties"]: None,
        SESSION_STATE_KEYS["original_prompt"]: "",
    }

    def __init__(self) -> None:
        logger.info("Initializing StreamlitChatbot")
        from app.services.llm_handler_service import LLMHandler ## Import LLMHandler locally to avoid circular import
        self.llm_handler = LLMHandler()
        self.specialty_handler = SpecialtyHandler(self.llm_handler)
        self.message_handler = MessageHandler(self.llm_handler, self.specialty_handler)
        self.ui_components = UIComponents(self._reset_session_state)
        self.MAX_MESSAGES = MAX_MESSAGES
    
    
    def _reset_session_state(self) -> None:
        """
        Reset all session state variables.
        """
        logger.info("Resetting session state")
        for key, value in self.SESSION_STATE_DEFAULTS.items():
            st.session_state[key] = value
    
    
    def _perform_sanity_checks(self, prompt: str, conversation: list = None, checks_to_run: list = None) -> None:
        """
        Perform selected sanity checks on user input using SanityChecksManager.
        """
        logger.debug("Starting sanity checks for user input")
        conv_history = ""
        if conversation is not None and len(conversation) > 0:
            conv_history = "\n".join([f"Utilisateur: {q}\nAssistant: {r}" for q, r in conversation])

        sanity_checks_manager = SanityChecksManager(self.llm_handler, max_messages=self.MAX_MESSAGES)
        # Default to all checks if not specified
        if checks_to_run is None:
            checks_to_run = DEFAULT_CHECKS_TO_RUN
        results = sanity_checks_manager.run_checks(prompt, conversation, conv_history, checks_to_run=checks_to_run)
        for check, result in results.items():
            if not result["passed"]:
                self._reset_session_state()
                st.warning(result["error"])
                st.stop()
        logger.debug("All sanity checks passed successfully")
    
    
    def _append_answer(self, prompt: str, specialty: str) -> None:
        """
        Generate and append answer to conversation.
        """
        try:
            from app.services.pipeline_orchestrator_service import PipelineOrchestrator ## Import PipelineOrchestrator locally to avoid circular import
            result, links = PipelineOrchestrator().generate_response(prompt=prompt, detected_specialty=specialty)
            formatted_result = format_links(result, links)
            result = execute_with_spinner(SPINNER_MESSAGES["loading"], lambda: formatted_result)
            append_to_conversation(prompt, result)
        except Exception as e:
            logger.error(f"Error in append_answer: {e}")
            st.error(ERROR_MESSAGES["response_generation"])
    
    
    def _handle_first_message(self):
        """        
        Handles the first user message, including sanity checks, specialty selection, and answer generation.
        """
        # Get user input
        user_input = st.chat_input(UI_CHAT_INPUT_PLACEHOLDER)
        if not user_input:
            return  # No input, nothing to do
    
        logger.info(f"Received first message - Prompt length: {len(user_input)} chars")
        st.session_state.prompt = user_input
        
        try:
            self._perform_sanity_checks(user_input)
            logger.debug("Sanity checks completed for first message")
        except Exception as e:
            logger.error(f"Sanity check failed for first message: {e}")
            return
        
        prompt = get_session_state_value(SESSION_STATE_KEYS["prompt"], "")
        
        # Handle specialty selection
        selected_specialty = self.specialty_handler.handle_specialty_selection(prompt)
        if selected_specialty:
            original_prompt = get_session_state_value(SESSION_STATE_KEYS["original_prompt"], prompt)
            self._append_answer(original_prompt, selected_specialty)
            return
        
        # Handle specialty selection UI if needed
        if get_session_state_value(SESSION_STATE_KEYS["multiple_specialties"], None) is not None:
            return
        
        # If prompt exists, handle answer generation
        if not prompt:
            return

        try:
            # Use previously selected specialty if available
            prev_specialty = get_session_state_value(SESSION_STATE_KEYS["selected_specialty"], None)
            if prev_specialty is not None:
                logger.info(f"Using previously selected specialty: {prev_specialty}")
                self._append_answer(prompt, st.session_state.selected_specialty)
                return

            # Detect specialty
            specialty, needs_rerun = self.specialty_handler.detect_and_handle_specialty(prompt)
            if needs_rerun:
                st.rerun()
                return

            self._append_answer(prompt, specialty)
        except Exception as e:
            logger.error(f"Error processing first message: {e}")
            st.error(ERROR_MESSAGES["general_processing"])
    
    
    def _handle_subsequent_messages(self):
        """
        Handle subsequent messages using 6-case approach.
        This method also checks if the user has selected a specialty, and if so, appends the answer accordingly.
        """
        # Handle specialty selection for subsequent messages
        selected_specialty = self.specialty_handler.handle_specialty_selection(
            get_session_state_value(SESSION_STATE_KEYS["prompt"], ""), 
            "_subsequent"
        )
        if selected_specialty:
            current_prompt = get_session_state_value(SESSION_STATE_KEYS["prompt"], "")
            self._append_answer(current_prompt, selected_specialty)
            return
        
        # Handle specialty selection UI if needed
        if get_session_state_value(SESSION_STATE_KEYS["multiple_specialties"], None) is not None:
            return
        
        user_input = st.chat_input(UI_CHAT_INPUT_PLACEHOLDER)
        if user_input:
            logger.info(f"Received subsequent message - Prompt length: {len(user_input)} chars, "
                    f"Conversation history: {get_conversation_length()} turns")
            
            st.session_state.prompt = user_input
            
            try:
                # Perform sanity checks
                current_conversation = get_conversation_list()
                self._perform_sanity_checks(user_input, current_conversation)
                logger.debug("Sanity checks completed for subsequent message")
                
                # Prepare conversation history
                # Pass conversation history to backend for multi-turn support
                self.message_handler.analyze_and_handle_message(user_input, current_conversation)
                
            except Exception as e:
                logger.error(f"Error processing subsequent message: {str(e)}")
                st.error(ERROR_MESSAGES["general_processing"])


    def run(self):
        """
        This method sets up the UI, initializes session state, checks conversation limits, and handles the first or subsequent messages based on the conversation history.
        It also displays the conversation history.
        """
        logger.info("Running StreamlitChatbot application")
        # Setup UI
        self.ui_components.setup_ui()
        # Initialize session state
        default_values = {
            SESSION_STATE_KEYS["conversation"]: [],
            SESSION_STATE_KEYS["selected_option"]: None,
            SESSION_STATE_KEYS["prompt"]: "",
            SESSION_STATE_KEYS["specialty"]: "",
            SESSION_STATE_KEYS["selected_specialty"]: None,
            SESSION_STATE_KEYS["specialty_context"]: None,
            SESSION_STATE_KEYS["multiple_specialties"]: None,
            SESSION_STATE_KEYS["original_prompt"]: "",
        }
        self.ui_components.setup_session_state(default_values)

        # Check conversation limit using SanityChecksManager
        sanity_checks_manager = SanityChecksManager(self.llm_handler)
        conversation = get_conversation_list()
        results = sanity_checks_manager.run_checks("", conversation, checks_to_run=["conversation_limit"])
        if not results["conversation_limit"]["passed"]:
            self._reset_session_state()
            st.warning(results["conversation_limit"]["error"])
            st.stop()

        # Handle messages
        if get_conversation_length() == 0:
            self._handle_first_message()
        else:
            self._handle_subsequent_messages()
        # Display conversation history
        display_conversation_history()


def main():
    """
    This function initializes the StreamlitChatbot and runs the application.
    """
    chatbot = StreamlitChatbot()
    chatbot.run()


if __name__ == "__main__":
    main()