""" 
number_institutions detection service.
-------------------------------
Detects the number of establishments (number_institutions) requested by users. 
"""

from app.config.features_config import number_institutions_DEFAULT, number_institutions_MIN, number_institutions_MAX
from app.utility.functions.llm_helpers import invoke_llm_with_error_handling, prompt_formatting, parse_llm_response
from app.utility.functions.logging import get_logger

logger = get_logger(__name__)


class number_institutionsDetector:
    """
    A class to detect the number of institutions requested by users in their prompts using a language model (LLM).
    Attributes:
        model: The language model to be used for detection.
        default_number_institutions: The default number of institutions if not specified.
        min_number_institutions: The minimum allowable number of institutions.
        max_number_institutions: The maximum allowable number of institutions.
    Methods:
        detect_number_institutions(prompt: str, conv_history: str = "") -> dict:
            Detects the number of institutions from the given prompt using the LLM. Returns a dict with keys 'number_institutions', 'detection_method', 'cost', and 'token_usage'.
    """
    
    def __init__(self, model):
        self.model = model
        self.default_number_institutions = number_institutions_DEFAULT
        self.min_number_institutions = number_institutions_MIN
        self.max_number_institutions = number_institutions_MAX


    def detect_number_institutions(self, prompt: str, conv_history: str = "") -> dict:
        """
        Detects the number_institutions results from the given prompt using the LLM.
        Returns a dict: {'number_institutions': int, 'detection_method': str, 'cost': float, 'token_usage': Any}
        """
        formatted_prompt = prompt_formatting("detect_number_institutions_prompt", prompt=prompt, conv_history=conv_history)
        llm_call_result = invoke_llm_with_error_handling(self.model, formatted_prompt, "detect_number_institutions")
        number_institutions_from_llm_call_response = llm_call_result.get('content', llm_call_result) if isinstance(llm_call_result, dict) else llm_call_result
        number_institutions = parse_llm_response(number_institutions_from_llm_call_response, "numeric", 0)
        
        cost = llm_call_result.get('cost', 0.0) if isinstance(llm_call_result, dict) else 0.0   
        token_usage = llm_call_result.get('token_usage', 0.0) if isinstance(llm_call_result, dict) else 0.0

        logger.debug(f"Number of institutions detection result: {number_institutions}, {cost}, {token_usage}")

        return {'number_institutions': number_institutions, 'detection_method': 'llm', 'cost': cost, 'token_usage': token_usage}