import json
from app.utility.logging import get_logger
from app.utility.llm_helpers import invoke_llm_with_error_handling
from app.utility.wrappers import prompt_formatting


logger = get_logger(__name__)


class InstitutionNamesDetector:
    """
    Responsible for extracting institution name or type from prompt using LLM.

    Attributes:
        model: The language model used for detection
        institution_list: Comma-separated list of valid institution names
        conv_history: Conversation history for context      

    Methods:
        detect_institution_names(prompt: str, institution_list: str, conv_history: str = "")
            Detects if a specific institution is mentioned in the prompt.
            Returns the institution name or "aucune correspondance" if not found.       
    """
    def __init__(self, model):
        self.model = model

    def detect_institution_names(self, prompt: str,  conv_history: str = "") -> dict:  # TODO : double check that i dont need institution list here
        """
        Detects if a specific institution is mentioned in the prompt.
        Returns a dict: {'institution_names': List[str], 'intent' ' str, 'detection_method': str, 'cost': float, 'token_usage': Any}
        """
        formatted_prompt = prompt_formatting("detect_institutions_prompt", prompt=prompt, conv_history=conv_history)
        llm_call_result = invoke_llm_with_error_handling(self.model, formatted_prompt, "detect_institution_names")
        content_str = llm_call_result.get('content', llm_call_result) if isinstance(llm_call_result, dict) else llm_call_result
        
        try:
            data = json.loads(content_str)
            institution_names = data.get("institutions", [])
            intent = data.get("intent", "none")
        except (json.JSONDecodeError, TypeError):
            institution_names = []
            intent = "none"
    
        cost = llm_call_result.get('cost', 0.0) if isinstance(llm_call_result, dict) else 0.0
        token_usage = llm_call_result.get('token_usage', 0.0) if isinstance(llm_call_result, dict) else 0.0

        logger.debug(f"Detected institutions: {institution_names}, intent: {intent}, cost: {cost}, token_usage: {token_usage}")
        
        return {'institution_names': institution_names, 'intent': intent, 'detection_method': 'llm', 'cost': cost, 'token_usage': token_usage}

