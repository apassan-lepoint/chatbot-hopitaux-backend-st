"""
Generic wrappers for sanity checks in Streamlit and FastAPI apps.
Use these to handle exceptions and apply framework-specific logic.
"""

import streamlit as st
from fastapi import HTTPException
from app.utility.prompt_instructions import PROMPT_INSTRUCTIONS
from enum import Enum
from app.utility.logging import get_logger

logger = get_logger(__name__)

from config.features_config import CityResponse, ModificationResponse, SpecialtyResponse
# # Streamlit generic wrapper
# def streamlit_check_wrapper(check_func, *args, reset_callback=None, **kwargs):
#     try:
#         check_func(*args, **kwargs)
#     except Exception as e:
#         if reset_callback:
#             reset_callback()
#         st.warning(str(e))
#         st.stop()

# # FastAPI generic wrapper
# def fastapi_check_wrapper(check_func, *args, **kwargs):
#     try:
#         check_func(*args, **kwargs)
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))



def parse_llm_response(response: str, response_type: str, default=None):
    """
    Unified parser for LLM responses.
    response_type: 'boolean', 'numeric', 'city', 'modification', 'institution_type', 'specialty'
    """
    try:
        resp = response.strip()
        if response_type == "boolean":
            return int(resp) == 1
        if response_type == "numeric":
            return int(resp)
        if response_type == "city":
            code = int(resp)
            valid = {
                CityResponse.NO_CITY_MENTIONED,
                CityResponse.FOREIGN,
                CityResponse.AMBIGUOUS,
                CityResponse.CITY_MENTIONED
            }
            return code if code in valid else CityResponse.NO_CITY_MENTIONED
        if response_type == "modification":
            code = int(resp)
            valid = {
                ModificationResponse.NEW_QUESTION,
                ModificationResponse.MODIFICATION,
                ModificationResponse.AMBIGUOUS
            }
            return code if code in valid else ModificationResponse.NEW_QUESTION
        if response_type == "institution_type":
            return {0: "no match", 1: "public", 2: "private"}.get(int(resp), "no match")
        if response_type == "specialty":
            return {
                0: SpecialtyResponse.NO_SPECIALTY_MENTIONED,
                1: SpecialtyResponse.SINGLE_SPECIALTY,
                2: SpecialtyResponse.MULTIPLE_SPECIALTIES
            }.get(int(resp), SpecialtyResponse.NO_SPECIALTY_MENTIONED)
        logger.warning(f"Unknown response_type: {response_type}")
        return default
    except (ValueError, AttributeError):
        logger.warning(f"Failed to parse {response_type} response: {response}")
        fallback = {
            "boolean": False,
            "numeric": default if default is not None else 0,
            "city": CityResponse.NO_CITY_MENTIONED,
            "modification": ModificationResponse.NEW_QUESTION,
            "institution_type": "no match",
            "specialty": SpecialtyResponse.NO_SPECIALTY_MENTIONED
        }
        return fallback.get(response_type, default)

def prompt_formatting(mode, **kwargs):
    """
    Generic wrapper for prompt formatting.
    Args:
        mode (str): Key for PROMPT_INSTRUCTIONS (e.g., 'detect_city_prompt', ...)
        kwargs: Arguments to format the template (prompt, conv_history, etc.)
    Returns:
        str: Formatted prompt
    """
    if mode not in PROMPT_INSTRUCTIONS:
        raise ValueError(f"Unknown prompt formatting mode: {mode}")
    return PROMPT_INSTRUCTIONS[mode].format(**kwargs)