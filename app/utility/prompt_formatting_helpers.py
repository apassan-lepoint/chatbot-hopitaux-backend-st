"""
Formatting helpers for LLM prompts and responses.
"""

def prompt_formatting(mode, **kwargs):
    """
    Formats prompts for LLM operations based on mode and keyword arguments.
    """
    # Example implementation, adapt as needed
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
    # Add more formatting modes as needed
    return str(kwargs)
