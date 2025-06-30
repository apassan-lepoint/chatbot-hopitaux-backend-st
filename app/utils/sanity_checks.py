"""
This module contains the sanity checks for streamlit.
"""

import streamlit as st
import logging

logger = logging.getLogger(__name__)

def check_message_length(message, reset_callback):
    """
    Check the length of the user message and reset session state if too long.
    
    Args:
        message (str): The user input message.
        reset_callback (function): Function to reset the session state.
    Raises:
        Warning: If the message is too long, a warning is displayed and the session state is
    """
    if len(message) > 200:
        reset_callback()
        st.warning("Votre message est trop long. Merci de reformuler.")
        st.stop()

def check_conversation_limit(conversation, max_messages, reset_callback):
    """
    Check if the conversation has reached the maximum number of messages.
        
    If so, reset the session state and notify the user.
    
    Args:
        conversation (list): The list of messages in the conversation.
        max_messages (int): The maximum number of messages allowed in the conversation.
        reset_callback (function): Function to reset the session state.
    Raises:
        Warning: If the conversation limit is reached, a warning is displayed and the session state is
            reset.
    """
    if len(conversation) >= max_messages:
        st.warning("La limite de messages a été atteinte. La conversation va redémarrer.")
        reset_callback()
        st.rerun()

def check_message_pertinence(user_input, appel_LLM, reset_callback, pertinent=False):
    """
    Checks if the user input is off-topic (standard or approfondi) and resets session state if so.

    Args:
        user_input (str): The user input message.
        appel_LLM (object): An instance of the Appels_LLM class.
        reset_callback (function): Function to reset the session state.
        pertinent (bool): If True, use the approfondi check and message.
    
    Raises:
        Warning: If the input is off-topic, a warning is displayed and the session state is
            reset.
    """
    logger.info(f"Checking if message is offtopic ({'approfondi' if pertinent else 'standard'}) for input: {user_input}")
    if pertinent:
        isofftopic = appel_LLM.check_chatbot_pertinence(user_input)
        match_str = 'hors sujet'
        warning_msg = (
            "Cet assistant a pour but de fournir des informations sur les classements des établissements de soins de cette année. Merci de reformuler."
        )
    else:
        isofftopic = appel_LLM.check_medical_pertinence(user_input)
        match_str = 'Hors sujet'
        warning_msg = "Je n'ai pas bien saisi la nature de votre demande. Merci de reformuler."
    if isofftopic == match_str:
        reset_callback()
        st.warning(warning_msg)
        st.stop()

def check_non_french_cities(user_input, appel_LLM, reset_callback):
    """
    Check if the user input contains a non-French city.
    
    Args:
        user_input (str): The user input message.
        appel_LLM (object): An instance of the Appels_LLM class to call the LLM methods.
        reset_callback (function): Function to reset the session state.
    Raises:     
        Warning: If a non-French city is detected, a warning is displayed and the session state is
            reset.
    """
    logger.info(f"Checking for non-French city in input: {user_input}")
    city = appel_LLM.get_city(user_input)
    if city == 'ville étrangère':
        reset_callback()
        st.warning(
            "Je ne peux pas répondre aux questions concernant les hôpitaux situés hors du territoire français, merci de consulter la page du palmarès. [🔗 Page du classement](https://www.lepoint.fr/hopitaux/classements)"
        )
        st.stop()
    if city == 'confusion':
        reset_callback()
        st.warning(
            "Je ne parviens pas à détecter votre localisation, merci de reformuler avec une autre ville."
        )
        st.stop()