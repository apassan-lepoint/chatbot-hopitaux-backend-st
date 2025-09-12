from app.utility.logging import get_logger
from app.utility.llm_helpers import invoke_llm_with_error_handling
from app.utility.wrappers import prompt_formatting


logger = get_logger(__name__)


class SpecialtyDetector:
    """
    Only detects specialty string and detection method.
    """
    def __init__(self, model):
        self.model = model

    def detect_specialty(self, prompt: str, conv_history: str = "") -> dict:
        """
        Returns a dict: {'specialty': str, 'detection_method': str, 'cost': float, 'token_usage': Any}
        """
        logger.info(f"Detecting specialty from prompt: '{prompt}'")
        # Step 1: LLM-based detection only
        formatted_prompt = prompt_formatting("second_detect_specialty_prompt", prompt=prompt, conv_history=conv_history)
        llm_call_result = invoke_llm_with_error_handling(self.model, formatted_prompt, "detect_specialty_llm")
        specialty = llm_call_result
        cost = 0.0
        token_usage = 0.0
        if isinstance(llm_call_result, dict):
            specialty = llm_call_result.get('content', llm_call_result)
            cost = llm_call_result.get('cost', 0.0)
            token_usage = llm_call_result.get('token_usage', 0.0)
        logger.info(f"Specialty detection result: {specialty}, method: llm")
        return {'specialty': specialty, 'detection_method': 'llm', 'cost': cost, 'token_usage': token_usage}
