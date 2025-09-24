"""
Utility functions for invoking LLMs with consistent error handling, logging, and token usage/cost tracking.
"""
import importlib
from langchain.schema import HumanMessage
from app.config.features_config import TRACK_LLM_CALL_COST, INPUT_PROMPT_PRICE_PER_TOKEN, OUTPUT_COMPLETION_PRICE_PER_TOKEN, NO_LOCATION_MENTIONED, LOCATION_FOREIGN, LOCATION_AMBIGUOUS, LOCATION_MENTIONED, MODIFICATION_NEW_QUESTION, MODIFICATION_MODIFICATION, MODIFICATION_AMBIGUOUS, SPECIALTY_NO_SPECIALTY_MENTIONED, SPECIALTY_SINGLE_SPECIALTY, SPECIALTY_MULTIPLE_SPECIALTIES
from app.utility.functions.logging import get_logger


logger = get_logger(__name__)


def _extract_token_usage_and_cost(response):
    """
    Extract token usage and compute cost from an LLM response.
    """
    token_usage = {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
    cost = 0.0

    if TRACK_LLM_CALL_COST:
        usage = response.llm_output.get("token_usage", {}) if response.llm_output else {}
        token_usage = {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }
        cost = (
            token_usage["prompt_tokens"] * INPUT_PROMPT_PRICE_PER_TOKEN +
            token_usage["completion_tokens"] * OUTPUT_COMPLETION_PRICE_PER_TOKEN
        )

    return token_usage, cost


def invoke_llm_with_error_handling(model, formatted_prompt, operation_name: str):
    """
    Invokes a ChatOpenAI LLM with consistent error handling, logging, and proper token usage/cost tracking.
    """
    try:
        # Wrap prompt in a HumanMessage for ChatOpenAI
        messages = [HumanMessage(content=formatted_prompt)]
        # Call the model and get full result
        response = model.generate(messages=[messages])
        # Extract the text content robustly
        content = response.generations[0][0].text.strip()
        # Extract token usage and cost
        token_usage, cost = _extract_token_usage_and_cost(response)

        logger.debug(f"LLM call '{operation_name}' successful: {token_usage}, cost={cost}")
        return {"content": content, "token_usage": token_usage, "cost": cost}

    except Exception as e:
        logger.error(f"LLM invocation failed in {operation_name}: {e}", exc_info=True)
        raise


def invoke_llm_and_parse_boolean(model, formatted_prompt, operation_name: str) -> bool:
    """
    Invoke a ChatOpenAI LLM, parse its response as a boolean, and track token usage/cost if enabled.
    """
    try:
        # Wrap prompt in a HumanMessage for ChatOpenAI
        messages = [HumanMessage(content=formatted_prompt)]
        # Call the model and get full result
        response = model.generate(messages=[messages])
        # Extract text content
        content = response.generations[0][0].text.strip()
        # Extract token usage and cost
        token_usage, cost = _extract_token_usage_and_cost(response)

        logger.debug(f"LLM call '{operation_name}' successful: {token_usage}, cost={cost}")
        return parse_llm_response(content, "boolean")

    except Exception as e:
        logger.error(f"LLM invocation failed in {operation_name}: {e}", exc_info=True)
        raise


def _load_all_prompt_instructions():
    """
    Loads and merges all *_PROMPT_INSTRUCTIONS dicts from 3 files.
    Returns:
        dict: Merged PROMPT_INSTRUCTIONS
    """
    merged = {}
    files = [
        "detection_prompt_instructions.py",
        "sanity_check_prompt_instructions.py",
        "conversation_prompt_instructions.py"
    ]
    for fname in files:
        mod_name = f"app.utility.prompt_instructions.{fname[:-3]}"
        mod = importlib.import_module(mod_name)
        for attr in dir(mod):
            if attr.endswith("_PROMPT_INSTRUCTIONS"):
                merged.update(getattr(mod, attr))
    return merged


def prompt_formatting(mode, **kwargs):
    """
    Formats a prompt based on the specified mode and keyword arguments.
    Returns the formatted prompt string.
    """
    PROMPT_INSTRUCTIONS = _load_all_prompt_instructions()

    if mode not in PROMPT_INSTRUCTIONS:
        raise ValueError(f"Unknown prompt formatting mode: {mode}")
    try:
        return PROMPT_INSTRUCTIONS[mode].format(**kwargs)
    except KeyError as e:
        logger.error(f"Missing key in prompt_formatting: {e}, kwargs: {kwargs}")
        raise


def parse_llm_response(response: str, response_type: str, default=None):
    """
    Unified parser for LLM responses.
    response_type: 'boolean', 'numeric', 'location', 'modification', 'institution_type', 'specialty'
    """
    try:
        resp = response.strip()
        if response_type == "boolean":
            resp_clean = resp.strip()
            if resp_clean in ("1", "0"):
                return int(resp_clean) == 1
            logger.warning(f"Boolean response not strictly 1 or 0: {resp_clean}")
            return default if default is not None else False
        if response_type == "numeric":
            return int(resp)
        if response_type == "location":
            code = int(resp)
            valid = {
                NO_LOCATION_MENTIONED,
                LOCATION_FOREIGN,
                LOCATION_AMBIGUOUS,
                LOCATION_MENTIONED
            }
            return code if code in valid else NO_LOCATION_MENTIONED
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
            "location": NO_LOCATION_MENTIONED,
            "modification": MODIFICATION_NEW_QUESTION,
            "institution_type": "no match",
            "specialty": SPECIALTY_NO_SPECIALTY_MENTIONED
        }
        return fallback.get(response_type, default)