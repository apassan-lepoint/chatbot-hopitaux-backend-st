from app.utility.logging import get_logger
from app.utility.llm_helpers import invoke_llm_with_error_handling
from app.utility.wrappers import prompt_formatting
from app.utility.wrappers import parse_llm_response

logger = get_logger(__name__)

class InstitutionTypeDetector:
    """
    Handles only detection/extraction of institution name and type from prompt using LLM.
    Attributes:
        model: The model used for detection.
        institution_list: A string representing the list of institutions.
    Methods:
        detect_institution_type(prompt: str, conv_history: str = "") -> str:
            Detects if the user has a preference for public or private institutions.
            Returns the raw LLM output (e.g., 'public', 'private', 'no match', etc.).
    """
    def __init__(self, model):
        self.model = model

    def detect_institution_type(self, prompt: str, conv_history: str = "") -> dict:
        """
        Detects if the user has a preference for public or private institutions.
        Returns a dict: {'institution_type': str, 'detection_method': str, 'cost': float, 'token_usage': Any}
        """
        formatted_prompt = prompt_formatting("detect_institution_type_prompt", prompt=prompt, conv_history=conv_history)
        llm_call_result = invoke_llm_with_error_handling(self.model, formatted_prompt, "detect_institution_type")
        institution_type_from_llm_call_response = llm_call_result.get('content', llm_call_result) if isinstance(llm_call_result, dict) else llm_call_result
        institution_type = parse_llm_response(institution_type_from_llm_call_response, "institution_type")

        cost = llm_call_result.get('cost', 0.0) if isinstance(llm_call_result, dict) else 0.0
        token_usage = llm_call_result.get('token_usage', 0.0) if isinstance(llm_call_result, dict) else 0.0

        logger.debug(f"Institution type detection result: {institution_type}, {cost}, {token_usage}")
        
        return {'institution_type': institution_type, 'detection_method': 'llm', 'cost': cost, 'token_usage': token_usage}

    

    