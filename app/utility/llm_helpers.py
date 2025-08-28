"""
Utility functions for invoking LLMs with consistent error handling, logging, and token usage/cost tracking.
"""
from langchain.schema import HumanMessage

from app.utility.logging import get_logger
from app.utility.wrappers import parse_llm_response
from app.config.features_config import TRACK_LLM_CALL_COST, INPUT_PROMPT_PRICE_PER_TOKEN, OUTPUT_COMPLETION_PRICE_PER_TOKEN


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
