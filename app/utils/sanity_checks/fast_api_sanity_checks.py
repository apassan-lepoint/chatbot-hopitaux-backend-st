"""
This module contains the sanity checks for FastAPI.
"""

from fastapi import HTTPException
from .core_logic_sanity_checks import (
    SanityCheckException,
    check_message_length_core,
    check_conversation_limit_core,
    sanity_check_message_pertinence_core,
    check_non_french_cities_core,
)

def check_message_length_fastapi(message):
    """
    Check the length of a message.  

    Args:
        message (str): The message to check.    
    
    Raises:
        HTTPException: If the message exceeds the maximum length, a 400 error is raised with a detailed message.
    """
    try:
        check_message_length_core(message)
    except SanityCheckException as e:
        raise HTTPException(status_code=400, detail=str(e))


def check_conversation_limit_fastapi(conversation, max_messages):
    """
    Check if the conversation has reached the maximum number of messages allowed.

    Args:
        conversation (list): The conversation to check.
        max_messages (int): The maximum number of messages allowed in the conversation. 
    
    Raises:
        HTTPException: If the conversation exceeds the maximum number of messages, a 400 error is raised with a detailed message.
    """
    try:
        check_conversation_limit_core(conversation, max_messages)
    except SanityCheckException as e:
        raise HTTPException(status_code=400, detail=str(e))


def sanity_check_message_pertinence_fastapi(user_input, llm_service, pertinent_chatbot_use_case=False, conv_history=""):
    """
    Check if the user input is off-topic (standard or pertinent) and raises an exception if it is.  
    
    Args:
        user_input (str): The user input to check.
        llm_service: The language model service used for checking pertinence.
        pertinent_chatbot_use_case (bool, optional): Additional check for pertinence. Defaults to False.
        conv_history (str, optional): Conversation history for context. Defaults to "".
        
    Raises:
        HTTPException: If the user input is off-topic, a 400 error is raised with a detailed message.   
    """
    try:
        sanity_check_message_pertinence_core(user_input, llm_service, pertinent_chatbot_use_case, conv_history)
    except SanityCheckException as e:
        raise HTTPException(status_code=400, detail=str(e))


def check_non_french_cities_fastapi(user_input, llm_service, conv_history=""):
    """
    Check if the user input contains non-French cities and raises an exception if it does.  
    
    Args:
        user_input (str): The user input to check.
        llm_service: The language model service used for checking non-French cities.
        conv_history (str, optional): Conversation history for context. Defaults to "".    
    
    Raises:
        HTTPException: If the user input contains non-French cities, a 400 error is raised with a detailed message.
        
    """
    try:
        check_non_french_cities_core(user_input, llm_service, conv_history)
    except SanityCheckException as e:
        raise HTTPException(status_code=400, detail=str(e))
