"""
Formatting helpers for LLM prompts and responses.
"""

def prompt_formatting_new(mode, **kwargs):
    """
    Formats prompts for LLM operations based on mode and keyword arguments.
    """
    from app.utility.prompt_instructions import PROMPT_INSTRUCTIONS
    if mode in PROMPT_INSTRUCTIONS:
        return PROMPT_INSTRUCTIONS[mode].format(**kwargs)
    # Fallback to previous behavior for legacy modes
    if mode == "continue_conversation_prompt":
        prompt = kwargs.get("prompt", "")
        conv_history = kwargs.get("conv_history", [])
        return f"Continue conversation: {prompt} | History: {conv_history}"
    elif mode == "detect_modification_prompt":
        prompt = kwargs.get("prompt", "")
        conv_history = kwargs.get("conv_history", [])
        return f"Detect modification: {prompt} | History: {conv_history}"
    elif mode == "merge_query_rewrite_prompt":
        prompt = kwargs.get("prompt", "")
        conv_history = kwargs.get("conv_history", "")
        return f"Merge query rewrite: {prompt} | History: {conv_history}"
    elif mode == "add_query_rewrite_prompt":
        prompt = kwargs.get("prompt", "")
        conv_history = kwargs.get("conv_history", "")
        return f"Add query rewrite: {prompt} | History: {conv_history}"
    # If mode is unknown, raise error for safety
    raise ValueError(f"Unknown prompt formatting mode: {mode}")
