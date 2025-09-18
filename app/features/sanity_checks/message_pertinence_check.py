"""
message_pertinence_check.py
--------------------------
This module defines the MessagePertinenceChecker class, which checks the pertinence of messages
using a large language model (LLM). 
"""

from app.config.features_config import ERROR_MESSAGES, METHODOLOGY_WEB_LINK
from app.utility.llm_helpers import invoke_llm_with_error_handling
from app.utility.logging import get_logger
from app.utility.wrappers import prompt_formatting, parse_llm_response


logger = get_logger(__name__)
class MessagePertinenceCheckException(Exception):
    pass

class MessagePertinenceChecker:
    """
    Class to check the pertinence of messages using a large language model (LLM).
    Attributes:
        llm_handler_service: Service to handle LLM interactions.
        pertinent_chatbot_use_case: Boolean indicating if the chatbot use case is pertinent.    
    Methods:
        sanity_check_medical_pertinence(prompt, conv_history): Checks if the prompt is medically pertinent.
        sanity_check_chatbot_pertinence(prompt, conv_history): Checks if the prompt is pertinent for the chatbot.
        check(user_input, conv_history): Runs both pertinence checks and returns standardized results.
    """
    def __init__(self, llm_handler_service, pertinent_chatbot_use_case=False):
        self.llm_handler_service = llm_handler_service
        self.pertinent_chatbot_use_case = pertinent_chatbot_use_case

    def sanity_check_medical_pertinence(self, prompt: str, conv_history: str = "") -> dict:
        """
        Checks the medical pertinence of the given prompt using the LLM.
        Returns True if medically pertinent, False otherwise.
        """
        formatted_prompt = prompt_formatting("sanity_check_medical_pertinence_prompt", prompt=prompt, conv_history=conv_history)
        logger.debug(f"Sanity check medical pertinence prompt sent to LLM.")
        result = invoke_llm_with_error_handling(self.llm_handler_service.model, formatted_prompt, "sanity_check_medical_pertinence")

        content = result.get('content') if isinstance(result, dict) else result
        parsed = parse_llm_response(content, "numeric")

        total_cost = result.get('cost') if isinstance(result, dict) else 0.0
        total_token_usage = result.get('token_usage', {}).get('total_tokens', 0) if isinstance(result, dict) else 0

        logger.debug(f"Raw LLM response for medical pertinence:\n{content}")
        logger.debug(f"Parsed medical pertinence value: {parsed} (type: {type(parsed)})")

        return {'result': parsed, 'cost': total_cost, 'token_usage': total_token_usage}

    def sanity_check_chatbot_pertinence(self, prompt: str, conv_history: str = "") -> dict:
        """
        Checks the pertinence of the given prompt for the chatbot using the LLM.
        Returns:
        "1" if relevant to chatbot,
        "0" if not relevant,
        "2" if methodology question.
        """
        formatted_prompt = prompt_formatting("sanity_check_chatbot_pertinence_prompt", prompt=prompt, conv_history=conv_history)
        logger.debug(f"Sanity check chatbot pertinence prompt sent to LLM.")
        
        result = invoke_llm_with_error_handling(self.llm_handler_service.model, formatted_prompt, "sanity_check_chatbot_pertinence")
        content = result.get('content') if isinstance(result, dict) else result
        parsed = parse_llm_response(content, "numeric")

        total_cost = result.get('cost') if isinstance(result, dict) else 0.0
        total_token_usage = result.get('token_usage', {}).get('total_tokens', 0) if isinstance(result, dict) else 0

        logger.debug(f"Raw LLM response for chatbot pertinence:\n{content}")
        logger.debug(f"Parsed chatbot pertinence value: {parsed} (type: {type(parsed)})")

        return {'result': parsed, 'cost': total_cost, 'token_usage': total_token_usage}
    
    def check(self, user_input, conv_history=""):
        """
        Checks if the user input is medically pertinent, then chatbot pertinent. Returns standardized dicts with cost, token_usage, and detection_method.
        """
        # First run medical pertinence check
        medical_pertinence_check_result = self.sanity_check_medical_pertinence(user_input, conv_history)
        logger.debug(f"medical_pertinence_result: {medical_pertinence_check_result}")

        if medical_pertinence_check_result['result'] == 0:  # Not medically pertinent
            return {"passed": False, "error": ERROR_MESSAGES["message_pertinence"], "cost": medical_pertinence_check_result["cost"], "token_usage": medical_pertinence_check_result["token_usage"]}

        elif medical_pertinence_check_result['result']== 2:  # Methodology question
            return {"passed": False, "error": ERROR_MESSAGES["methodology_questions"], "cost": medical_pertinence_check_result["cost"], "token_usage": medical_pertinence_check_result["token_usage"]}

        # Next run chatbot pertinence check if medically pertinent
        chatbot_pertinence_check_result = self.sanity_check_chatbot_pertinence(user_input, conv_history)
        if chatbot_pertinence_check_result["result"] == 0:
            return {"passed": False, "error": ERROR_MESSAGES["message_pertinence"], "cost": chatbot_pertinence_check_result["cost"], "token_usage": chatbot_pertinence_check_result["token_usage"]}
    
        return {"passed": True, "cost": medical_pertinence_check_result["cost"] + chatbot_pertinence_check_result["cost"], "token_usage": medical_pertinence_check_result["token_usage"] + chatbot_pertinence_check_result["token_usage"]}