"""
This module contains sanity checks that are used in both the Streamlit and Fast API applications.
"""

import streamlit as st
import logging
from app.utils.query_detection.response_parser import CityResponse

logger = logging.getLogger(__name__)

class SanityCheckException(Exception):
    """
    Custom exception for sanity checks in the application.  
    This exception is raised when a sanity check fails, indicating that the input or state does not meet the required conditions.
    It is not intended to be used directly by users, but rather as part of the application's error handling and validation mechanisms.
    """
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


def sanity_check_message_pertinence_core(user_input, llm_service, pertinent_chatbot_use_case=False, conv_history=""):
    """
    Checks if the user input is off-topic (standard or pertinent) and raises an exception if it is.
    
    Args:
        user_input: The user's message
        llm_service: LLM service instance
        pertinent_chatbot_use_case: Whether to use advanced pertinence check
        conv_history: Optional conversation history for context
    """
    logger.info(f"Checking if message is offtopic ({'pertinent' if pertinent_chatbot_use_case else 'standard'}) for input: {user_input}")
    if pertinent_chatbot_use_case:
        is_off_topic = not llm_service.sanity_check_chatbot_pertinence(user_input, conv_history)
        warning_msg = (
            "Cet assistant a pour but de fournir des informations sur les classements des établissements de soins de cette année. Merci de reformuler."
        )
    else:
        is_off_topic = not llm_service.sanity_check_medical_pertinence(user_input, conv_history)
        warning_msg = "Je n'ai pas bien saisi la nature de votre demande. Merci de reformuler."
    
    if is_off_topic:
        raise SanityCheckException(warning_msg)


def check_non_french_cities_core(user_input, llm_service, conv_history=""):
    """
    Checks for non-French cities in user input.
    
    Args:
        user_input: The user's message
        llm_service: LLM service instance
        conv_history: Optional conversation history for context
    """
    logger.info(f"Checking for non-French city in input: {user_input}")
    city = llm_service.detect_city(user_input, conv_history)
    if city == CityResponse.FOREIGN:
        raise SanityCheckException(
            "Je ne peux pas répondre aux questions concernant les hôpitaux situés hors du territoire français, merci de consulter la page du palmarès. [🔗 Page du classement](https://www.lepoint.fr/hopitaux/classements)"
        )
    if city == CityResponse.AMBIGUOUS:
        raise SanityCheckException(
            "Je ne parviens pas à détecter votre localisation, merci de reformuler avec une autre ville."
        )