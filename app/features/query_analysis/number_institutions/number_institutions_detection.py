from app.utility.logging import get_logger
from app.utility.llm_helpers import invoke_llm_with_error_handling
from app.utility.wrappers import prompt_formatting
from app.utility.wrappers import parse_llm_response
from app.config.features_config import number_institutions_DEFAULT, number_institutions_MIN, number_institutions_MAX

logger = get_logger(__name__)


class number_institutionsDetector:
    """
    Service for detecting the number of establishments (number_institutions) requested by users.
    Handles detection from user messages with conversation context support.
    Uses a language model to interpret the request and extract the number of institutions.  
    Supports default values and range constraints.
    Attributes:
        model: The language model used for detection.
        default_number_institutions: Default value if not specified by user.
        min_number_institutions: Minimum allowed value for number of institutions.
        max_number_institutions: Maximum allowed value for number of institutions.
    Methods:
        detect_number_institutions(prompt: str, conv_history: str = "") -> int:
            Detects the number of institutions from the given prompt using the LLM.
        detect_number_institutions_with_fallback(prompt: str, conv_history: str = "", as_string: bool = False) -> int | str:
            Detects number of institutions with fallback to default value or string.
            If as_string=True, returns string or 'non mentionné'
            if not specified by user.
            Otherwise returns integer for number of institutions or default value.
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
        logger.debug(f"Detecting number_institutions from prompt: {prompt[:50]}...")
        formatted_prompt = prompt_formatting("detect_number_institutions_prompt", prompt=prompt, conv_history=conv_history)
        raw_response = invoke_llm_with_error_handling(self.model, formatted_prompt, "detect_number_institutions")
        cost = 0.0
        token_usage = 0.0
        number_institutions = raw_response
        if isinstance(raw_response, dict):
            cost = raw_response.get('cost', 0.0)
            number_institutions = raw_response.get('content', raw_response)
            token_usage = raw_response.get('token_usage', 0.0)
        parsed_number = parse_llm_response(number_institutions, "numeric", 0)
        return {'number_institutions': parsed_number, 'detection_method': 'llm', 'cost': cost, 'token_usage': token_usage}
    def detect_number_institutions_with_fallback(self, prompt: str, conv_history: str = "", as_string: bool = False) -> int | str:
        """
        Detects number_institutions with fallback to default value or string.
        If as_string=True, returns string or 'non mentionné'.
        """
        detected_number_institutions = self.detect_number_institutions(prompt, conv_history)
        if as_string:
            return str(detected_number_institutions) if detected_number_institutions > 0 else 'non mentionné'
        return detected_number_institutions if detected_number_institutions > 0 else self.default_number_institutions

