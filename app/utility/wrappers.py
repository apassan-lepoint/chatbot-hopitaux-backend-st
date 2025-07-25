"""
Generic wrappers for sanity checks in Streamlit and FastAPI apps.
Use these to handle exceptions and apply framework-specific logic.
"""


from app.utility.prompt_instructions import PROMPT_INSTRUCTIONS
from app.utility.logging import get_logger

logger = get_logger(__name__)

from app.config.features_config import (
    CITY_NO_CITY_MENTIONED,
    CITY_FOREIGN,
    CITY_AMBIGUOUS,
    CITY_MENTIONED,
    MODIFICATION_NEW_QUESTION,
    MODIFICATION_MODIFICATION,
    MODIFICATION_AMBIGUOUS,
    SPECIALTY_NO_SPECIALTY_MENTIONED,
    SPECIALTY_SINGLE_SPECIALTY,
    SPECIALTY_MULTIPLE_SPECIALTIES
)


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
                CITY_NO_CITY_MENTIONED,
                CITY_FOREIGN,
                CITY_AMBIGUOUS,
                CITY_MENTIONED
            }
            return code if code in valid else CITY_NO_CITY_MENTIONED
        if response_type == "modification":
            code = int(resp)
            valid = {
                MODIFICATION_NEW_QUESTION,
                MODIFICATION_MODIFICATION,
                MODIFICATION_AMBIGUOUS
            }
            return code if code in valid else MODIFICATION_NEW_QUESTION
        if response_type == "institution_type":
            return {0: "no match", 1: "public", 2: "private"}.get(int(resp), "no match")
        if response_type == "specialty":
            return {
                0: SPECIALTY_NO_SPECIALTY_MENTIONED,
                1: SPECIALTY_SINGLE_SPECIALTY,
                2: SPECIALTY_MULTIPLE_SPECIALTIES
            }.get(int(resp), SPECIALTY_NO_SPECIALTY_MENTIONED)
        logger.warning(f"Unknown response_type: {response_type}")
        return default
    except (ValueError, AttributeError):
        logger.warning(f"Failed to parse {response_type} response: {response}")
        fallback = {
            "boolean": False,
            "numeric": default if default is not None else 0,
            "city": CITY_NO_CITY_MENTIONED,
            "modification": MODIFICATION_NEW_QUESTION,
            "institution_type": "no match",
            "specialty": SPECIALTY_NO_SPECIALTY_MENTIONED
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

## KEEP BELOW FUNTIONS UNTIL POST TESTING 
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