from app.config.features_config import MAX_MESSAGES, MAX_LENGTH
from app.features.sanity_checks.conversation_limit_check import ConversationLimitChecker, ConversationLimitCheckException
from app.features.sanity_checks.message_length_check import MessageLengthChecker, MessageLengthCheckException
from app.features.sanity_checks.message_pertinence_check import MessagePertinenceChecker, MessagePertinenceCheckException
from app.utility.logging import get_logger

logger = get_logger(__name__)


class SanityChecksAnalyst:
    """
    Analyst for running various sanity checks on user input and conversation history.
    This class encapsulates checks for conversation limits, message length, and message pertinence.

    Attributes:
        conversation_checker (ConversationLimitChecker): Checks if the conversation exceeds the maximum message limit.
        length_checker (MessageLengthChecker): Checks if the user input exceeds the maximum length.
        pertinence_checker (MessagePertinenceChecker): Checks if the user input is pertinent to the chatbot use case.
    Methods:
        run_checks(user_input, conversation, conv_history="", checks_to_run=None):
            Runs the selected checks and returns their results.
    """
    def __init__(self, llm_handler_service, max_messages=MAX_MESSAGES, max_length=MAX_LENGTH, pertinent_chatbot_use_case=False):
        logger.info("Initializing SanityChecksAnalyst")
        self.conversation_checker = ConversationLimitChecker(max_messages)
        self.length_checker = MessageLengthChecker(max_length)
        self.pertinence_checker = MessagePertinenceChecker(llm_handler_service, pertinent_chatbot_use_case)

    def run_checks(self, user_input, conversation, conv_history="", checks_to_run=None):
        """
        Run selected checks and return their results.
        """
        all_checks = {
            "conversation_limit": lambda: self.conversation_checker.check(conversation),
            "message_length": lambda: self.length_checker.check(user_input),
            "message_pertinence": lambda: self.pertinence_checker.check(user_input, conv_history)
        }
        
        if checks_to_run is None:
            checks_to_run = list(all_checks.keys())

        logger.debug(f"run_checks called: user_input={user_input}, conversation={conversation}, conv_history={conv_history}, checks_to_run={checks_to_run}")
        
        results = {}
        all_passed = True
        
        logger.info(f"SanityChecksAnalyst running checks: {checks_to_run} for user_input: {user_input}")
        for check_name in checks_to_run:
            try:
                check_result = all_checks[check_name]()
                results[check_name] = check_result
                passed = check_result.get("passed", False)
                if not passed:
                    # Halt the pipeline
                    raise Exception(check_result.get("error", f"{check_name} failed"))
                
            except (ConversationLimitCheckException, MessageLengthCheckException) as e:
                logger.info(f"Sanity check exception caught: {str(e)}. Stopping pipeline.")
                results[check_name] = {"passed": False, "error": str(e), "detection_method": "rule"}
                all_passed = False  

        # Get total cost/tokens from pertinence checker only
        pertinence = results.get("message_pertinence", {})
        total_cost = pertinence.get("cost", 0.0)
        total_tokens = pertinence.get("token_usage", 0)

        results["passed"] = all_passed
        results["total_cost"] = total_cost
        results["total_tokens"] = total_tokens

        logger.info(f"SanityChecksAnalyst completed checks. All passed: {all_passed}, Total cost: {total_cost}, Total tokens: {total_tokens}")
        logger.info(f"Sanity check results: {results}")
        return results
