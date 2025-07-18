class MessagePertinenceCheckException(Exception):
    pass

class MessagePertinenceChecker:
    def __init__(self, llm_handler_service, pertinent_chatbot_use_case=False):
        self.llm_handler_service = llm_handler_service
        self.pertinent_chatbot_use_case = pertinent_chatbot_use_case

    def check(self, user_input, conv_history=""):
        """
        Checks if the user input is off-topic (standard or pertinent) and raises an exception if it is.

        Args:
            user_input (str): The user's message
            conv_history (str, optional): Conversation history for context

        Raises:
            MessagePertinenceCheckException: If the message is off-topic.
        """
        if self.pertinent_chatbot_use_case:
            is_off_topic = not self.llm_handler_service.sanity_check_chatbot_pertinence(user_input, conv_history)
            warning_msg = (
                "Cet assistant a pour but de fournir des informations sur les classements des établissements de soins de cette année. Merci de reformuler."
            )
        else:
            is_off_topic = not self.llm_handler_service.sanity_check_medical_pertinence(user_input, conv_history)
            warning_msg = "Je n'ai pas bien saisi la nature de votre demande. Merci de reformuler."

        if is_off_topic:
            raise MessagePertinenceCheckException(warning_msg)
