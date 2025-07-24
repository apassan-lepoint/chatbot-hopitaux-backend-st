from app.config.features_config import WARNING_MESSAGES


class MessagePertinenceCheckException(Exception):
    pass

class MessagePertinenceChecker:
    def __init__(self, llm_handler_service, pertinent_chatbot_use_case=False):
        self.llm_handler_service = llm_handler_service
        self.pertinent_chatbot_use_case = pertinent_chatbot_use_case

    def sanity_check_medical_pertinence(self, prompt: str, conv_history: str = "") -> str:
        """
        Checks the medical pertinence of the given prompt using the LLM.
        Returns True if medically pertinent, False otherwise.
        Args:
            prompt: The message to check
            conv_history: Optional conversation history for context
        """
        from app.utility.wrappers import prompt_formatting ## Import prompt_formatting locally to avoid circular import
        formatted_prompt = prompt_formatting(
            "sanity_check_medical_pertinence_prompt",
            prompt=prompt,
            conv_history=conv_history
        )
        from app.utility.llm_helpers import invoke_llm_and_parse_boolean ## Import invoke_llm_and_parse_boolean locally to avoid circular import
        return invoke_llm_and_parse_boolean(self.llm_handler_service.model, formatted_prompt, "sanity_check_medical_pertinence")

    def sanity_check_chatbot_pertinence(self, prompt: str, conv_history: str = "") -> str:
        """
        Checks the pertinence of the given prompt for the chatbot using the LLM.
        Returns True if relevant to chatbot, False otherwise.
        """
        from app.utility.wrappers import prompt_formatting
        formatted_prompt = prompt_formatting(
            "sanity_check_chatbot_pertinence_prompt",
            prompt=prompt,
            conv_history=conv_history
        )
        from app.utility.llm_helpers import invoke_llm_and_parse_boolean
        return invoke_llm_and_parse_boolean(self.llm_handler_service.model, formatted_prompt, "sanity_check_chatbot_pertinence")
    
    def check(self, user_input, conv_history=""):
        """
        Checks if the user input is medically pertinent, then chatbot pertinent. Raises an exception if either is off-topic.
        """
        # First, check medical pertinence
        is_medically_pertinent = self.sanity_check_medical_pertinence(user_input, conv_history)
        if not is_medically_pertinent:
            raise MessagePertinenceCheckException(WARNING_MESSAGES["message_pertinence"])

        # Then, check chatbot pertinence
        is_chatbot_pertinent = self.sanity_check_chatbot_pertinence(user_input, conv_history)
        if not is_chatbot_pertinent:
            raise MessagePertinenceCheckException(WARNING_MESSAGES["message_pertinence"])
