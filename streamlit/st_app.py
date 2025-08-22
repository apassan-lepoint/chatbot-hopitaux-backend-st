"""
Main Streamlit-based user interface for the hospital ranking chatbot.
"""

import sys
import os
import streamlit as st
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.features.sanity_checks.sanity_checks_analyst import SanityChecksAnalyst
from app.utility.logging import get_logger
from st_config import (SESSION_STATE_KEYS, SESSION_STATE_DEFAULTS, MAX_MESSAGES, UI_CHAT_INPUT_PLACEHOLDER)
from st_utility import (display_conversation_history, get_conversation_list, get_conversation_length, get_session_state_value, handle_specialty_selection, process_message)
from st_ui_components import UIComponents
from app.services.llm_handler_service import LLMHandler



logger = get_logger(__name__)


class StreamlitChatbot:
    """
    Main class for the Streamlit-based hospital ranking chatbot application.
    This class initializes the application, sets up the UI, handles user input, performs sanity checks, and manages the conversation flow.
    """
    def __init__(self) -> None:
        logger.info("Initializing StreamlitChatbot")
        self.ui_components = UIComponents(self._reset_session_state)
        self.max_messages = MAX_MESSAGES
        self.llm_handler = LLMHandler()


    def _reset_session_state(self) -> None:
        """
        Reset the session state to its default values and remove any extra keys.
        """
        logger.info("Resetting session state")
        # Force clear conversation before setting defaults
        st.session_state[SESSION_STATE_KEYS["conversation"]] = []
        for key, value in SESSION_STATE_DEFAULTS.items():
            st.session_state[key] = value
        extra_keys = [k for k in st.session_state.keys() if k not in SESSION_STATE_DEFAULTS]
        for k in extra_keys:
            del st.session_state[k]
        logger.info(f"Session state after reset: {st.session_state}")
    

    def _handle_first_message(self):
        """
        Handles the first message from the user: gets input and calls MessageHandler to process.
        """
        # try:
        user_input = st.chat_input(UI_CHAT_INPUT_PLACEHOLDER)
        if not user_input and st.session_state.prompt:
            user_input = st.session_state.prompt
        if not user_input:
            return
        logger.info(f"First message user_input: '{user_input}'")
        st.session_state.prompt = user_input
        prompt = get_session_state_value(SESSION_STATE_KEYS["prompt"], "")
        process_message(prompt)
    
    
    def _handle_subsequent_messages(self):
        """
        Handles subsequent messages from the user: gets input and calls MessageHandler to process.
        """
        user_input = st.chat_input(UI_CHAT_INPUT_PLACEHOLDER)
        if not user_input and st.session_state.prompt:
            user_input = st.session_state.prompt
        if not user_input:
            return
        logger.info(f"Subsequent message user_input: '{user_input}'")
        st.session_state.prompt = user_input
        prompt = get_session_state_value(SESSION_STATE_KEYS["prompt"], "")
        self.message_handler.process_message(prompt)



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

        if st.session_state.get("multiple_specialties") is not None:
            st.info("[DEBUG] Entered specialty selection block")
            st.info(f"[DEBUG] multiple_specialties: {st.session_state['multiple_specialties']}")
            st.info(f"[DEBUG] type(multiple_specialties): {type(st.session_state['multiple_specialties'])}")
            multiple_specialties = st.session_state["multiple_specialties"]
            if not isinstance(multiple_specialties, list):
                st.error("Erreur: la liste des spécialités n'est pas au format attendu. Type: {} Value: {}".format(type(multiple_specialties), multiple_specialties))
                st.info("[DEBUG] Exiting due to invalid type for multiple_specialties")
                return
            key_suffix = f"_{get_conversation_length()}"
            st.info(f"[DEBUG] Rendering specialty form with key_suffix: {key_suffix}")
            with st.form("specialty_form"):
                st.info("[DEBUG] Inside specialty_form context")
                selected_specialty = st.radio(
                    "Veuillez sélectionner une spécialité pour continuer.",
                    multiple_specialties,
                    index=0,
                    key=f"specialty_radio{key_suffix}"
                )
                st.info(f"[DEBUG] Radio rendered, current value: {selected_specialty}")
                submit = st.form_submit_button("Valider")
                st.info(f"[DEBUG] Form submit button pressed: {submit}")
                st.info(f"[DEBUG] selected_specialty after submit: {selected_specialty}")
                if submit:
                    st.info(f"[DEBUG] Form submitted, processing selection")
                    if selected_specialty:
                        st.info(f"[DEBUG] Valid specialty selected: {selected_specialty}")
                        st.session_state.selected_specialty = selected_specialty
                        st.session_state.specialty_context = {
                            'original_query': st.session_state.get("prompt", ""),
                            'selected_specialty': selected_specialty,
                            'timestamp': datetime.now().isoformat()
                        }
                        st.session_state.multiple_specialties = None
                        st.info(f"[DEBUG] Updated session_state after specialty selection: {st.session_state}")
                        process_message(st.session_state.get("prompt", ""))
                    else:
                        st.info("[DEBUG] No specialty selected, showing info message")
                        st.info("Veuillez sélectionner une spécialité avant de poursuivre.")
            st.info("[DEBUG] Exiting specialty selection block, blocking further UI")
            # Return here to block further UI until specialty is selected
            return
        
        # Handle messages
        if get_conversation_length() == 0:
            self._handle_first_message()
        else:
            self._handle_subsequent_messages()
        # Only display conversation history if there is something to show
        if get_conversation_length() > 0:
            display_conversation_history()


def main():
    """
    This function initializes the StreamlitChatbot and runs the application.
    """
    chatbot = StreamlitChatbot()
    chatbot.run()


if __name__ == "__main__":
    main()
