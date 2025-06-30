"""
This module contains the sanity checks for Streamlit.
"""

import streamlit as st
import logging
from .core_logic_sanity_checks import (
    SanityCheckException,
    check_message_length_core,
    check_conversation_limit_core,
    check_message_pertinence_core,
    check_non_french_cities_core,
)

logger = logging.getLogger(__name__)

def check_message_length_streamlit(message, reset_callback):
    try:
        check_message_length_core(message)
    except SanityCheckException as e:
        reset_callback()
        st.warning(str(e))
        st.stop()

def check_conversation_limit_streamlit(conversation, max_messages, reset_callback):
    try:
        check_conversation_limit_core(conversation, max_messages)
    except SanityCheckException as e:
        st.warning(str(e))
        reset_callback()
        st.rerun()

def check_message_pertinence_streamlit(user_input, appel_LLM, reset_callback, pertinence_check2=False):
    try:
        check_message_pertinence_core(user_input, appel_LLM, pertinence_check2)
    except SanityCheckException as e:
        reset_callback()
        st.warning(str(e))
        st.stop()

def check_non_french_cities_streamlit(user_input, appel_LLM, reset_callback):
    try:
        check_non_french_cities_core(user_input, appel_LLM)
    except SanityCheckException as e:
        reset_callback()
        st.warning(str(e))
        st.stop()