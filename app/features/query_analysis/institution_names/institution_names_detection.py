""" 
institution_names_detection.py
---------------------------------
This module contains the InstitutionNamesDetector class which is responsible for detecting institution names
from user prompts using a language model (LLM).
"""

import json 
import re
from app.utility.functions.llm_helpers import invoke_llm_with_error_handling
from app.utility.functions.logging import get_logger
from app.utility.functions.llm_helpers import prompt_formatting


logger = get_logger(__name__)


class InstitutionNamesDetector:
    """
    Class to detect institution names from user prompts using a language model (LLM).   
    Attributes:
        model: The language model to be used for detection.         
    Methods:
        detect_institution_names(prompt: str, conv_history: str = "") -> dict:
            Detects if a specific institution is mentioned in the prompt.
    """
    def __init__(self, model):
        self.model = model


    def detect_institution_names(self, prompt: str, conv_history: str = "") -> dict:  # TODO : double check that i dont need institution list here
        """
        Detects if a specific institution is mentioned in the prompt.
        Returns a dict: {'institution_names': List[str], 'intent' ' str, 'detection_method': str, 'cost': float, 'token_usage': Any}
        """
        logger.debug(f"Detecting institution names in prompt: {prompt!r} with conv_history: {conv_history!r}")

        formatted_prompt = prompt_formatting("detect_institutions_prompt", prompt=prompt, conv_history=conv_history)
        # logger.debug(f"Formatted prompt for LLM: {formatted_prompt!r}")
        llm_call_result = invoke_llm_with_error_handling(self.model, formatted_prompt, "detect_institution_names")
        # logger.debug(f"LLM call result: {llm_call_result!r}")
        content_str = llm_call_result.get('content', llm_call_result) if isinstance(llm_call_result, dict) else llm_call_result

        logger.debug(f"Raw LLM response: {content_str!r}")

        # Try to extract JSON object using regex
        json_str = None
        if isinstance(content_str, str):
            content_str = content_str.strip()
            match = re.search(r'\{.*\}', content_str, re.DOTALL)
            if match:
                json_str = match.group(0)
            else:
                json_str = content_str  # fallback

        logger.debug(f"Cleaned LLM response for JSON: {json_str!r}")

        try:
            data = json.loads(json_str)
            logger.debug(f"Type after json.loads: {type(data)} | Value: {data}")
            institution_names = data.get("institutions", []) if isinstance(data, dict) else []
            intent = data.get("intent", "none") if isinstance(data, dict) else "none"
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to parse LLM response as JSON: {e} | Raw: {content_str!r} | Cleaned: {json_str!r}")
            institution_names = []
            intent = "none"
    
        cost = llm_call_result.get('cost', 0.0) if isinstance(llm_call_result, dict) else 0.0
        token_usage = llm_call_result.get('token_usage', 0.0) if isinstance(llm_call_result, dict) else 0.0

        logger.debug(f"Detected institutions: {institution_names}, intent: {intent}, cost: {cost}, token_usage: {token_usage}")
        # logger.debug(f"Type and value of institution_names before validation: {type(institution_names)} | {institution_names}") 
        
        return {'institution_names': institution_names, 'intent': intent, 'detection_method': 'llm', 'cost': cost, 'token_usage': token_usage}

