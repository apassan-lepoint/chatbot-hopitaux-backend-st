
from app.config.features_config import WARNING_MESSAGES, METHODOLOGY_WEB_LINK
from app.utility.logging import get_logger
from app.utility.wrappers import prompt_formatting, parse_llm_response
from app.utility.llm_helpers import invoke_llm_with_error_handling

class MessagePertinenceCheckException(Exception):
    """
    Exception raised when a message fails the pertinence check.
    """
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

    def sanity_check_medical_pertinence(self, prompt: str, conv_history: str = "") -> str:
        """
        Checks the medical pertinence of the given prompt using the LLM.
        Returns True if medically pertinent, False otherwise.
        """
        formatted_prompt = prompt_formatting(
            "sanity_check_medical_pertinence_prompt",
            prompt=prompt,
            conv_history=conv_history
        )
        logger = get_logger(__name__)
        logger.debug(f"Sanity check medical pertinence prompt sent to LLM.")
        raw_response = invoke_llm_with_error_handling(self.llm_handler_service.model, formatted_prompt, "sanity_check_medical_pertinence")
        logger.debug(f"Raw LLM response for medical pertinence:\n{raw_response}")
        return parse_llm_response(raw_response, "string")

    def sanity_check_chatbot_pertinence(self, prompt: str, conv_history: str = "") -> str:
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
        raw_response = invoke_llm_with_error_handling(self.llm_handler_service.model, formatted_prompt, "sanity_check_chatbot_pertinence")
        logger.debug(f"Raw LLM response for chatbot pertinence:\n{raw_response}")
        return parse_llm_response(raw_response, "string")
    
    def check(self, user_input, conv_history=""):
        """
        Checks if the user input is medically pertinent, then chatbot pertinent. Raises an exception if either is off-topic.
        """
        # First, check medical pertinence
        medically_pertinent_result = self.sanity_check_medical_pertinence(user_input, conv_history)
        if medically_pertinent_result == '0':
            raise MessagePertinenceCheckException(WARNING_MESSAGES["message_pertinence"])
        elif medically_pertinent_result == '2':
            return MessagePertinenceCheckException(WARNING_MESSAGES["methodology_questions"].format(METHODOLOGY_WEB_LINK=METHODOLOGY_WEB_LINK))
        
        # Then, check chatbot pertinence
        chatbot_pertinence_result = self.sanity_check_chatbot_pertinence(user_input, conv_history)    
        if chatbot_pertinence_result == "0":
            # Standardized response for non-relevant questions
            raise MessagePertinenceCheckException(WARNING_MESSAGES["message_pertinence"])
