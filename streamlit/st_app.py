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
        logger.info("Resetting session state (safe)")
        # Explicitly clear conversation
        st.session_state[SESSION_STATE_KEYS["conversation"]] = []
        # Only set defaults for missing keys
        for key, value in SESSION_STATE_DEFAULTS.items():
            if key not in st.session_state:
                st.session_state[key] = value
        logger.info(f"Session state after safe reset: {st.session_state}")
    

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
        Handles subsequent messages from the user: gets input and calls process_message to handle specialty selection and backend response.
        """
        user_input = st.chat_input(UI_CHAT_INPUT_PLACEHOLDER)
        if not user_input and st.session_state.prompt:
            user_input = st.session_state.prompt
        if not user_input:
            return
        logger.info(f"Subsequent message user_input: '{user_input}'")
        st.session_state.prompt = user_input
        prompt = get_session_state_value(SESSION_STATE_KEYS["prompt"], "")
        process_message(prompt)



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
        
        # Handle messages
        if get_conversation_length() == 0:
            self._handle_first_message()
        else:
            self._handle_subsequent_messages()
        # Always display conversation history after processing a message
        display_conversation_history()


def main():
    """
    This function initializes the StreamlitChatbot and runs the application.
    """
    chatbot = StreamlitChatbot()
    chatbot.run()


if __name__ == "__main__":
    main()
