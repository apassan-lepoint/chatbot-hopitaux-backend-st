import streamlit as st
from typing import Any, Callable
from datetime import datetime
import logging

from st_config import (SESSION_STATE_KEYS, UI_SPECIALTY_SELECTION_PROMPT, UI_INVALID_SELECTION_ERROR, SPINNER_MESSAGES, ERROR_MESSAGES)
from app.utility.logging import get_logger
from app.utility.formatting_helpers import format_links
from app.services.pipeline_orchestrator_service import PipelineOrchestrator


logger = get_logger(__name__)

# --- Session state initialization: only set defaults if not already present ---
def initialize_session_state():
    defaults = {
        'conversation': [],
        'selected_option': None,
        'prompt': '',
        'specialty': '',
        'selected_specialty': None,
        'specialty_context': None,
        'multiple_specialties': None,
        'original_prompt': ''
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

initialize_session_state()


def handle_specialty_selection(prompt: str, key_suffix: str = "") -> str:
    """
    Displays a radio button for the user to select a specialty from a list (provided by backend).
    Updates session state with the selected specialty.
    """
    multiple_specialties = get_session_state_value(SESSION_STATE_KEYS["multiple_specialties"], None)
    logger.info(f"[handle_specialty_selection] multiple_specialties in session: {multiple_specialties}")
    # Defensive: ensure multiple_specialties is a list
    if multiple_specialties is not None:
        if not isinstance(multiple_specialties, list):
            # Try to convert to list if it's a string (comma separated)
            if isinstance(multiple_specialties, str):
                multiple_specialties = [s.strip() for s in multiple_specialties.split(",") if s.strip()]
                st.session_state.multiple_specialties = multiple_specialties
            else:
                st.error("Erreur: la liste des spécialités n'est pas au format attendu.")
                return None
        if not multiple_specialties:
            st.error("Aucune spécialité à sélectionner.")
            return None
        selected_specialty = st.radio(
            UI_SPECIALTY_SELECTION_PROMPT,
            multiple_specialties,
            index=0,
            key=f"specialty_radio{key_suffix}"
        )
        logger.info(f"[handle_specialty_selection] selected_specialty: {selected_specialty}")
        # Process selection immediately when radio changes
        if selected_specialty and selected_specialty in multiple_specialties:
            st.session_state.selected_specialty = selected_specialty
            st.session_state.specialty_context = {
                'original_query': prompt,
                'selected_specialty': selected_specialty,
                'timestamp': datetime.now().isoformat()
            }
            logger.info(f"[handle_specialty_selection] Clearing multiple_specialties after selection: {selected_specialty}")
            st.session_state.multiple_specialties = None
            st.rerun()
            return selected_specialty
        elif selected_specialty:
            st.error(UI_INVALID_SELECTION_ERROR)
    return None

def process_message(prompt: str) -> None:
    """
    This function sends the user's prompt to the backend, optionally including a selected specialty.
    If multiple specialties are detected, it blocks further processing and prompts the user to select one.
    The selected specialty is stored in session state and used for subsequent queries.
    The function also handles backend responses that may again require specialty selection, and appends
    the conversation turn to the session history.
    """
    logger.info(f"[process_message] multiple_specialties in session: {st.session_state.get('multiple_specialties')}")
    # Always preserve the prompt in session state
    if prompt:
        st.session_state.prompt = prompt
    # If multiple_specialties is present, always show the specialty selection UI and block further processing until a valid selection
    if st.session_state.get("multiple_specialties") is not None:
        selected_specialty = handle_specialty_selection(st.session_state.prompt)
        if not selected_specialty:
            st.info("Veuillez sélectionner une spécialité avant de poursuivre.")
            logger.info("[process_message] Blocking further processing due to multiple_specialties.")
            st.stop()  # Ensures UI is rendered and blocks further code execution
        # Specialty was just selected, rerun will happen, so return here
        logger.info(f"[process_message] User selected specialty: {selected_specialty}")
        return
    # If specialty was just selected and multiple_specialties is now None, generate response
    prev_specialty = st.session_state.get("selected_specialty")
    if prev_specialty and st.session_state.get("multiple_specialties") is None:
        logger.info(f"[process_message] Using previous selected_specialty: {prev_specialty}")
        result, links = PipelineOrchestrator().generate_response(prompt=st.session_state.prompt, detected_specialty=prev_specialty)
        if isinstance(result, dict) and "multiple_specialties" in result:
            logger.info(f"[process_message] Backend returned multiple_specialties again: {result['multiple_specialties']}")
            st.session_state["multiple_specialties"] = result["multiple_specialties"]
            st.info(result["message"])
            st.rerun()  # Force rerun so specialty selection UI is rendered immediately
            return
        formatted_result = format_links(result, links)
        result = execute_with_spinner(SPINNER_MESSAGES["loading"], lambda: formatted_result)
        append_to_conversation(st.session_state.prompt, result)
        return
    prev_specialty = st.session_state.get("selected_specialty")
    if prev_specialty:
        logger.info(f"[process_message] Using previous selected_specialty: {prev_specialty}")
        result, links = PipelineOrchestrator().generate_response(prompt=st.session_state.prompt, detected_specialty=prev_specialty)
        if isinstance(result, dict) and "multiple_specialties" in result:
            logger.info(f"[process_message] Backend returned multiple_specialties again: {result['multiple_specialties']}")
            st.session_state["multiple_specialties"] = result["multiple_specialties"]
            st.info(result["message"])
            st.rerun()  # Force rerun so specialty selection UI is rendered immediately
            return
        formatted_result = format_links(result, links)
        result = execute_with_spinner(SPINNER_MESSAGES["loading"], lambda: formatted_result)
        append_to_conversation(st.session_state.prompt, result)
        return
    try:
        result, links = PipelineOrchestrator().generate_response(prompt=st.session_state.prompt)
        if isinstance(result, dict) and "multiple_specialties" in result:
            logger.info(f"[process_message] Backend returned multiple_specialties: {result['multiple_specialties']}")
            st.session_state["multiple_specialties"] = result["multiple_specialties"]
            st.info(result["message"])
            st.rerun()  # Force rerun so specialty selection UI is rendered immediately
            return
        formatted_result = format_links(result, links)
        result = execute_with_spinner(SPINNER_MESSAGES["loading"], lambda: formatted_result)
        append_to_conversation(st.session_state.prompt, result)
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        st.error(ERROR_MESSAGES["general_processing"])


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
