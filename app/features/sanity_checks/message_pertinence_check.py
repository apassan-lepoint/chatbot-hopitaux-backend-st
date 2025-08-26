
from app.config.features_config import WARNING_MESSAGES, METHODOLOGY_WEB_LINK
from app.utility.logging import get_logger
from app.utility.wrappers import prompt_formatting, parse_llm_response
from app.utility.llm_helpers import invoke_llm_with_error_handling


logger = get_logger(__name__)
class MessagePertinenceCheckException(Exception):
    pass

class MessagePertinenceChecker:
    """
    Class to check the pertinence of messages using an LLM.
    This class provides methods to check if a message is medically pertinent
    and if it is relevant for the chatbot use case.
    It uses the LLM handler service to invoke the model with formatted prompts
    and parse the responses.

    Attributes:
        llm_handler_service: Service to handle LLM interactions.
        pertinent_chatbot_use_case: Flag to indicate if the chatbot use case is pertinent.
    Methods:
        sanity_check_medical_pertinence(prompt: str, conv_history: str = "") -> str:
            Checks the medical pertinence of the given prompt.
        sanity_check_chatbot_pertinence(prompt: str, conv_history: str = "") -> str:
            Checks the pertinence of the given prompt for the chatbot.
        check(user_input, conv_history=""):
            Checks if the user input is medically pertinent and chatbot pertinent.
            Raises MessagePertinenceCheckException if either check fails.
    """
    def __init__(self, llm_handler_service, pertinent_chatbot_use_case=False):
        self.llm_handler_service = llm_handler_service
        self.pertinent_chatbot_use_case = pertinent_chatbot_use_case

    def sanity_check_medical_pertinence(self, prompt: str, conv_history: str = "") -> dict:
        """
        Checks the medical pertinence of the given prompt using the LLM.
        Returns True if medically pertinent, False otherwise.
        """
        formatted_prompt = prompt_formatting(
            "sanity_check_medical_pertinence_prompt",
            prompt=prompt,
            conv_history=conv_history
        )
        logger.debug(f"Sanity check medical pertinence prompt sent to LLM.")
        result = invoke_llm_with_error_handling(self.llm_handler_service.model, formatted_prompt, "sanity_check_medical_pertinence")
        if isinstance(result, dict):
            content = result.get('content')
            cost = result.get('cost')
            total_tokens = result.get('token_usage', {}).get('total_tokens', 0)
        else:
            content = result
            cost = None
            token_usage = 0
        logger.debug(f"Raw LLM response for medical pertinence:\n{content}")
        parsed = parse_llm_response(content, "numeric")
        logger.debug(f"Parsed medical pertinence value: {parsed} (type: {type(parsed)})")
        return {'result': parsed, 'cost': cost, 'token_usage': token_usage}

    def sanity_check_chatbot_pertinence(self, prompt: str, conv_history: str = "") -> dict:
        """
        Checks the pertinence of the given prompt for the chatbot using the LLM.
        Returns:
        "1" if relevant to chatbot,
        "0" if not relevant,
        "2" if methodology question.
        """
        formatted_prompt = prompt_formatting(
            "sanity_check_chatbot_pertinence_prompt",
            prompt=prompt,
            conv_history=conv_history
        )
        logger = get_logger(__name__)
        logger.debug(f"Sanity check chatbot pertinence prompt sent to LLM.")
        result = invoke_llm_with_error_handling(self.llm_handler_service.model, formatted_prompt, "sanity_check_chatbot_pertinence")
        if isinstance(result, dict):
            content = result.get('content')
            cost = result.get('cost')
            total_tokens = result.get('token_usage', {}).get('total_tokens', 0)
        else:
            content = result
            cost = None
            token_usage = 0
        logger.debug(f"Raw LLM response for chatbot pertinence:\n{content}")
        parsed = parse_llm_response(content, "numeric")
        logger.debug(f"Parsed chatbot pertinence value: {parsed} (type: {type(parsed)})")
        return {'result': parsed, 'cost': cost, 'token_usage': token_usage}
    
    def check(self, user_input, conv_history=""):
        """
        Checks if the user input is medically pertinent, then chatbot pertinent. Returns standardized dicts with cost, token_usage, and detection_method.
        """
        med_result = self.sanity_check_medical_pertinence(user_input, conv_history)
        logger.debug(f"med_result: {med_result}")
        med_passed = bool(med_result.get('result', False))
        med_cost = med_result.get('cost', 0.0)
        med_token_usage = med_result.get('token_usage', {}).get('total_tokens', 0)
        if not med_passed:
            return {"passed": False, "error": WARNING_MESSAGES["message_pertinence"], "cost": med_cost, "token_usage": med_token_usage, "detection_method": "llm-medical"}
        chatbot_result = self.sanity_check_chatbot_pertinence(user_input, conv_history)
        logger.debug(f"chatbot_result: {chatbot_result}")
        chatbot_value = chatbot_result.get('result', 0)
        chatbot_cost = chatbot_result.get('cost', 0.0)
        chatbot_token_usage = chatbot_result.get('token_usage', {}).get('total_tokens', 0)
        if chatbot_value == 2:
            # Methodology question: halt pipeline and return specific warning
            return {"passed": False, "error": WARNING_MESSAGES["methodology_questions"], "cost": chatbot_cost, "token_usage": chatbot_token_usage, "detection_method": "llm-chatbot-methodology"}
        if chatbot_value == 0:
            return {"passed": False, "error": WARNING_MESSAGES["message_pertinence"], "cost": chatbot_cost, "token_usage": chatbot_token_usage, "detection_method": "llm-chatbot"}
        return {"passed": True, "cost": med_cost + chatbot_cost, "token_usage": med_token_usage + chatbot_token_usage, "detection_method": "llm-both"}
