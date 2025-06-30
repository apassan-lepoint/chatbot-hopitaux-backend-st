"""
This module contains sanity checks that are used in both the Streamlit and Fast API applications.
"""

import streamlit as st
import logging

logger = logging.getLogger(__name__)

class SanityCheckException(Exception):
    """Custom exception for sanity check failures."""
    pass

def check_message_length_core(message, max_length=200):
    """
    Checks if the length of the message exceeds the maximum allowed length.

    Args:
        message (_type_): _description_
        max_length (int, optional): _description_. Defaults to 200.

    Raises:
        SanityCheckException: _description_
    """
    if len(message) > max_length:
        raise SanityCheckException("Votre message est trop long. Merci de reformuler.")

def check_conversation_limit_core(conversation, max_messages):
    """
    Checks if the conversation has reached the maximum number of messages allowed.

    Args:
        conversation (_type_): _description_
        max_messages (_type_): _description_

    Raises:
        SanityCheckException: _description_
    """
    if len(conversation) >= max_messages:
        raise SanityCheckException("La limite de messages a été atteinte. La conversation va redémarrer.")

def check_message_pertinence_core(user_input, appel_LLM, pertinence_check2=False):
    """
    Checks if the user input is off-topic (standard or pertinent) and raises an exception if it is.

    Args:
        user_input (_type_): _description_
        appel_LLM (_type_): _description_
        pertinence_check2 (bool, optional): _description_. Defaults to False.

    Raises:
        SanityCheckException: _description_
    """
    logger.info(f"Checking if message is offtopic ({'pertinent' if pertinence_check2 else 'standard'}) for input: {user_input}")
    if pertinence_check2:
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
        raise SanityCheckException(warning_msg)

def check_non_french_cities_core(user_input, appel_LLM):
    logger.info(f"Checking for non-French city in input: {user_input}")
    city = appel_LLM.get_city(user_input)
    if city == 'ville étrangère':
        raise SanityCheckException(
            "Je ne peux pas répondre aux questions concernant les hôpitaux situés hors du territoire français, merci de consulter la page du palmarès. [🔗 Page du classement](https://www.lepoint.fr/hopitaux/classements)"
        )
    if city == 'confusion':
        raise SanityCheckException(
            "Je ne parviens pas à détecter votre localisation, merci de reformuler avec une autre ville."
        )