"""
Streamlit-specific sanity check functions that wrap core validation logic with UI feedback.
Provides user-friendly error handling and interface controls for message validation in the Streamlit app.
"""

import streamlit as st
import logging
from .core_logic_sanity_checks import (
    SanityCheckException,
    check_message_length_core,
    check_conversation_limit_core,
    sanity_check_message_pertinence_core,
    check_non_french_cities_core,
)

logger = logging.getLogger(__name__)

def check_message_length_streamlit(message, reset_callback):
    """
    Validates message length and displays warning in Streamlit UI if validation fails.
    
    Args:
        message (str): User message to validate.
        reset_callback (callable): Function to reset application state.
        
    Raises:
        Stops Streamlit execution if message length is invalid.
    """
    try:
        check_message_length_core(message)
    except SanityCheckException as e:
        reset_callback()
        st.warning(str(e))
        st.stop()

def check_conversation_limit_streamlit(conversation, max_messages, reset_callback):
    """
    Validates conversation length limit and triggers app reset if exceeded.
    
    Args:
        conversation (list): Current conversation history.
        max_messages (int): Maximum allowed messages in conversation.
        reset_callback (callable): Function to reset application state.
        
    Raises:
        Triggers Streamlit rerun if conversation limit exceeded.
    """
    try:
        check_conversation_limit_core(conversation, max_messages)
    except SanityCheckException as e:
        st.warning(str(e))
        reset_callback()
        st.rerun()

def sanity_check_message_pertinence_streamlit(user_input, llm_service, reset_callback, pertinent_chatbot_use_case=False, conv_history=""):
    """
    Validates message relevance to hospital topics using LLM service.
    
    Args:
        user_input (str): User's input message to validate.
        llm_service: LLM service instance for relevance checking.
        reset_callback (callable): Function to reset application state.
        pertinent_chatbot_use_case (bool, optional): Enable secondary pertinence check. Defaults to False.
        conv_history (str, optional): Conversation history for context. Defaults to "".
        
    Raises:
        Stops Streamlit execution if message is not relevant to hospital topics.
    """
    try:
        sanity_check_message_pertinence_core(user_input, llm_service, pertinent_chatbot_use_case, conv_history)
    except SanityCheckException as e:
        reset_callback()
        st.warning(str(e))
        st.stop()

def check_non_french_cities_streamlit(user_input, llm_service, reset_callback, conv_history=""):
    """
    Validates that mentioned cities are French locations using LLM service.
    
    Args:
        user_input (str): User's input message to validate.
        llm_service: LLM service instance for city validation.
        reset_callback (callable): Function to reset application state.
        conv_history (str, optional): Conversation history for context. Defaults to "".
        
    Raises:
        Stops Streamlit execution if non-French cities are detected.
    """
    try:
        check_non_french_cities_core(user_input, llm_service, conv_history)
    except SanityCheckException as e:
        reset_callback()
        st.warning(str(e))
        st.stop()