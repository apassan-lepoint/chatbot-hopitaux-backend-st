"""
Utility functions for Streamlit session state management.

This module provides helper functions for common Streamlit patterns
used in the chatbot UI.
"""

import streamlit as st

from typing import Dict, Any, Optional, Callable
from app.utility.logging import get_logger

logger = get_logger(__name__)


def append_to_conversation(user_input: str, bot_response: str) -> None:
    logger.debug(f"Appending to conversation: user_input='{user_input}', bot_response='{bot_response[:50]}...")
    """
    Append a user-bot interaction to the conversation history.
    
    Args:
        user_input: The user's input message
        bot_response: The bot's response
    """
    if "conversation" not in st.session_state:
        st.session_state.conversation = []
    st.session_state.conversation.append((user_input, bot_response))


def create_example_button(question: str, button_key: str, 
                        help_text: str = "Cliquez pour poser cette question") -> bool:
    """
    Create an example question button that updates session state when clicked.
    
    Args:
        question: The example question text
        button_key: Unique key for the button
        help_text: Help text to show on hover
        
    Returns:
        bool: True if button was clicked
    """
    if st.button(question, key=button_key, help=help_text, type="primary"):
        st.session_state.prompt = question
        st.chat_message("user").write(question)
        st.rerun()
        return True
    return False


def display_conversation_history() -> None:
    logger.debug(f"Displaying conversation history: {st.session_state.get('conversation', [])}")
    """
    Display the conversation history with chat-like styling.
    """
    if "conversation" in st.session_state:
        for user, bot in st.session_state.conversation:
            logger.debug(f"Rendering user: '{user}', bot: '{bot[:50]}...'")
            st.chat_message("user").write(user)
            st.chat_message("assistant").write(bot, unsafe_allow_html=True)


def format_conversation_history_for_llm() -> str:
    """
    Format conversation history for LLM context.
    
    Returns:
        str: Formatted conversation history
    """
    if "conversation" not in st.session_state or not st.session_state.conversation:
        return ""
    
    return "\n".join(
        [f"Utilisateur: {q}\nAssistant: {r}" for q, r in st.session_state.conversation]
    )


def execute_with_spinner(spinner_text: str, func: Callable, *args, **kwargs) -> Any:
    logger.debug(f"Executing with spinner: '{spinner_text}'")
    """
    Execute a function with a loading spinner.
    
    Args:
        spinner_text: Text to display in the spinner
        func: Function to execute
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        The result of the function execution
    """
    with st.spinner(spinner_text):
        return func(*args, **kwargs)


def check_session_state_exists(key: str) -> bool:
    """
    Check if a key exists in session state.
    
    Args:
        key: The key to check
        
    Returns:
        bool: True if key exists, False otherwise
    """
    return key in st.session_state


def get_session_state_value(key: str, default_value: Any = None) -> Any:
    """
    Get a value from session state with optional default.
    
    Args:
        key: The key to retrieve
        default_value: Default value if key doesn't exist
        
    Returns:
        The value from session state or default value
    """
    return st.session_state.get(key, default_value)


def get_conversation_list() -> list:
    """
    Get the conversation list from session state.
    
    Returns:
        list: The conversation history as a list of tuples
    """
    return st.session_state.get("conversation", [])


def get_conversation_length() -> int:
    """
    Get the length of the conversation history.
    
    Returns:
        int: Number of conversation turns
    """
    return len(st.session_state.get("conversation", []))
