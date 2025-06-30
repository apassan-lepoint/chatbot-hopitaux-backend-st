"""
This module contains the sanity checks for FastAPI.
"""

from fastapi import HTTPException
from .core_logic_sanity_checks import (
    SanityCheckException,
    check_message_length_core,
    check_conversation_limit_core,
    check_message_pertinence_core,
    check_non_french_cities_core,
)

def check_message_length_fastapi(message):
    try:
        check_message_length_core(message)
    except SanityCheckException as e:
        raise HTTPException(status_code=400, detail=str(e))

def check_conversation_limit_fastapi(conversation, max_messages):
    try:
        check_conversation_limit_core(conversation, max_messages)
    except SanityCheckException as e:
        raise HTTPException(status_code=400, detail=str(e))

def check_message_pertinence_fastapi(user_input, llm_service, pertinence_check2=False):
    try:
        check_message_pertinence_core(user_input, llm_service, pertinence_check2)
    except SanityCheckException as e:
        raise HTTPException(status_code=400, detail=str(e))

def check_non_french_cities_fastapi(user_input, llm_service):
    try:
        check_non_french_cities_core(user_input, llm_service)
    except SanityCheckException as e:
        raise HTTPException(status_code=400, detail=str(e))