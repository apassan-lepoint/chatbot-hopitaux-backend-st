from app.config.features_config import MAX_MESSAGES, MAX_LENGTH
from app.features.sanity_checks.conversation_limit_check import ConversationLimitChecker, ConversationLimitCheckException
from app.features.sanity_checks.message_length_check import MessageLengthChecker, MessageLengthCheckException
from app.features.sanity_checks.message_pertinence_check import MessagePertinenceChecker, MessagePertinenceCheckException

class SanityChecksManager:
    def __init__(self, llm_handler_service, max_messages=MAX_MESSAGES, max_length=MAX_LENGTH, pertinent_chatbot_use_case=False):
        self.conversation_checker = ConversationLimitChecker(max_messages)
        self.length_checker = MessageLengthChecker(max_length)
        self.pertinence_checker = MessagePertinenceChecker(llm_handler_service, pertinent_chatbot_use_case)

    def run_checks(self, user_input, conversation, conv_history="", checks_to_run=None):
        """
        Run selected checks and return their results.
        checks_to_run: list of check names to run (default: all)
        """
        all_checks = {
            "conversation_limit": lambda: self.conversation_checker.check(conversation),
            "message_length": lambda: self.length_checker.check(user_input),
            "message_pertinence": lambda: self.pertinence_checker.check(user_input, conv_history),
        }
        if checks_to_run is None:
            checks_to_run = list(all_checks.keys())
        results = {}
        for check_name in checks_to_run:
            try:
                all_checks[check_name]()
                results[check_name] = {"passed": True}
            except (ConversationLimitCheckException, MessageLengthCheckException, MessagePertinenceCheckException) as e:
                results[check_name] = {"passed": False, "error": str(e)}
        return results
