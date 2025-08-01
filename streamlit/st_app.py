"""
Main Streamlit-based user interface for the hospital ranking chatbot.
"""

import sys
import os
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.features.sanity_checks.sanity_checks_analyst import SanityChecksAnalyst
from app.utility.logging import get_logger
from app.utility.formatting_helpers import format_links

from st_config import (DEFAULT_CHECKS_TO_RUN, SESSION_STATE_KEYS, SESSION_STATE_DEFAULTS, MAX_MESSAGES, UI_CHAT_INPUT_PLACEHOLDER, ERROR_MESSAGES, SPINNER_MESSAGES)
from st_utility import (append_to_conversation, display_conversation_history, get_conversation_list, get_conversation_length, get_session_state_value, execute_with_spinner)
from st_message_handler import MessageHandler
from st_specialty_handler import SpecialtyHandler
from st_ui_components import UIComponents


logger = get_logger(__name__)


class StreamlitChatbot:
    """
    Main class for the Streamlit-based hospital ranking chatbot application.
    This class initializes the application, sets up the UI, handles user input, performs sanity checks, and manages the conversation flow.
    """
    def __init__(self) -> None:
        logger.info("Initializing StreamlitChatbot")
        from app.services.llm_handler_service import LLMHandler ## Import LLMHandler locally to avoid circular import
        self.llm_handler = LLMHandler()
        self.specialty_handler = SpecialtyHandler(self.llm_handler)
        self.message_handler = MessageHandler(self.llm_handler, self.specialty_handler)
        self.ui_components = UIComponents(self._reset_session_state)
        self.max_messages = MAX_MESSAGES
    
    
    def _reset_session_state(self) -> None:
        """
        Reset the session state to its default values.
        """
        logger.info("Resetting session state")
        for key, value in SESSION_STATE_DEFAULTS.items():
            st.session_state[key] = value
    
    
    def _perform_sanity_checks(self, prompt: str, conversation: list = None, checks_to_run: list = None) -> None:
        """
        Perform sanity checks on the user input and conversation history.
        """
        logger.debug("Starting sanity checks for user input")

        # Ensure conversation is always a list, never None
        if conversation is None:
            conversation = []
        conv_history = ""
        if len(conversation) > 0:
            conv_history = "\n".join([f"Utilisateur: {q}\nAssistant: {r}" for q, r in conversation])

        sanity_checks_manager = SanityChecksAnalyst(self.llm_handler, max_messages=self.max_messages)
        # Default to all checks if not specified
        if checks_to_run is None:
            checks_to_run = DEFAULT_CHECKS_TO_RUN
        results = sanity_checks_manager.run_checks(prompt, conversation, conv_history, checks_to_run=checks_to_run)
        for check, result in results.items():
            if not result["passed"]:
                append_to_conversation(prompt, "")  # Show user input with empty response
                self._reset_session_state()
                st.warning(result["error"])
                st.stop()
        logger.debug("All sanity checks passed successfully")
    
    
    def _append_answer(self, prompt: str, specialty: str) -> None:
        """
        This method uses the PipelineOrchestrator to generate a response based on the prompt and detected specialty.
        It also formats the result and appends it to the conversation history.
        If an error occurs during response generation, it logs the error and displays an error message to the user.
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
        This method handles the first message from the user.
        It retrieves the user input, performs sanity checks, detects the specialty, and appends the answer to the conversation history.
        If the user input is empty, it returns without doing anything.
        If the user has selected a specialty, it appends the answer accordingly.
        If the user input is not empty, it performs sanity checks and detects the specialty.
        If the specialty is detected, it appends the answer to the conversation history.
        If an error occurs during any of these steps, it logs the error and displays an error message to the user.  
        """
        # Get user input
        user_input = st.chat_input(UI_CHAT_INPUT_PLACEHOLDER)
        if not user_input and st.session_state.prompt:
            user_input = st.session_state.prompt
        if not user_input:
            return  # No input, nothing to do
        logger.info(f"First message user_input: '{user_input}'")
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
        This method handles subsequent messages from the user.
        It retrieves the user input, checks if a specialty has been selected, and appends the answer to the conversation history.
        If a specialty is selected, it appends the answer accordingly.
        If the user input is empty, it returns without doing anything.
        If the user has selected a specialty, it appends the answer accordingly.
        If the user input is not empty, it performs sanity checks and appends the answer to the conversation history.
        If an error occurs during any of these steps, it logs the error and displays an error message to the user.
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
            logger.info(f"Subsequent message user_input: '{user_input}'")
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
        This method runs the StreamlitChatbot application.
        It sets up the UI, initializes the session state, performs sanity checks, and handles user messages.
        If the conversation limit is reached, it resets the session state and displays a warning message.
        If this is the first message, it handles the first message input.
        If there are subsequent messages, it handles them accordingly.
        Finally, it displays the conversation history.  
        """
        logger.info("Running StreamlitChatbot application")
        # Setup UI
        self.ui_components.setup_ui()
        # Initialize session state
        self.ui_components.setup_session_state(SESSION_STATE_DEFAULTS)

        # Check conversation limit using SanityChecksAnalyst
        sanity_checks_manager = SanityChecksAnalyst(self.llm_handler)
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