from app.features.conversation.llm_responder import LLMResponder
from app.features.conversation.multi_turn import MultiTurn
from app.features.sanity_checks.sanity_checks_analyst import SanityChecksAnalyst
from app.utility.logging import get_logger
from app.config.features_config import ENABLE_MULTI_TURN, ERROR_MESSAGES, CHECKS_TO_RUN_MULTI_TURN

logger = get_logger(__name__)

class ConversationAnalyst:
    """
    Class to analyze conversations using LLMResponder and MultiTurn.
    It provides methods to run various conversation checks and consolidate results.
    Attributes:
        model: The language model used for conversation analysis.
    Methods:
        run_all_conversation_checks(prompt: str, conv_history: list) -> dict:
            Runs all conversation-related checks and returns a consolidated dictionary of results.
    """
    def __init__(self, model):
        logger.info("Initializing ConversationAnalyst")
        self.model = model
        self.conversation = LLMResponder(model)
        self.multi_turn = MultiTurn(model) if ENABLE_MULTI_TURN else None

    def run_all_conversation_checks(self, prompt: str, conv_history: list) -> dict:
        logger.debug(f"Running all conversation checks: prompt={prompt}, conv_history={conv_history}")
        """
        Runs all conversation-related checks and consolidates results into a dictionary with the following keys:
        - 'continued_response': Result of continuing the conversation.
        - 'modification_result': Result of detecting query modification.
        - 'multi_turn_result': Result of analyzing subsequent messages in a multi-turn conversation (if enabled).
        """
        # Ensure conv_history is a list of messages for sanity checks
        conversation_list = conv_history if isinstance(conv_history, list) else []
        sanity_analyst = SanityChecksAnalyst(self.model)
        results = sanity_analyst.run_checks(prompt, conversation_list, conv_history, checks_to_run=CHECKS_TO_RUN_MULTI_TURN)
        failed = next((k for k, v in results.items() if not v["passed"]), None)
        if failed:
            return {
                "continued_response": None,
                "modification_result": None,
                "multi_turn_result": None,
                "sanity_check_failed": True,
                "warning_message": ERROR_MESSAGES.get(failed, "Votre message n'est pas accepté.")
            }
        # Run Conversation methods
        continued_response = self.conversation.continue_conversation(prompt, conv_history)
        continued_cost = 0.0
        continued_method = "llm"
        continued_tokens = None
        if isinstance(continued_response, dict):
            continued_cost = continued_response.get('cost', 0.0)
            continued_method = continued_response.get('detection_method', 'llm')
            continued_tokens = continued_response.get('token_usage', {}).get('total_tokens', 0)

        modification_result = self.conversation.detect_query_modification(prompt, conv_history)
        # If modification_result is a dict, extract cost, method, tokens
        modification_cost = 0.0
        modification_method = "llm"
        modification_tokens = None
        if isinstance(modification_result, dict):
            modification_cost = modification_result.get('cost', 0.0)
            modification_method = modification_result.get('detection_method', 'llm')
            modification_tokens = modification_result.get('token_usage', {}).get('total_tokens', 0)

        # Multi-turn conversation analysis
        multi_turn_result = None
        multi_turn_cost = 0.0
        multi_turn_method = None
        multi_turn_tokens = None
        if ENABLE_MULTI_TURN and self.multi_turn:
            multi_turn_result = self.multi_turn.analyze_subsequent_message(prompt, conv_history)
            if isinstance(multi_turn_result, dict):
                multi_turn_cost = multi_turn_result.get('cost', 0.0)
                multi_turn_method = multi_turn_result.get('detection_method', 'llm')
                multi_turn_tokens = multi_turn_result.get('token_usage', {}).get('total_tokens', 0)

        total_cost = (
            continued_cost
            + modification_cost
            + multi_turn_cost
        )
        total_token_usage = (
            (continued_tokens or 0)
            + (modification_tokens or 0)
            + (multi_turn_tokens or 0)
        )
        consolidated = {
            "continued_response": continued_response,
            "continued_response_cost": continued_cost,
            "continued_response_detection_method": continued_method,
            "continued_response_tokens": continued_tokens,
            "modification_result": modification_result,
            "modification_result_cost": modification_cost,
            "modification_result_detection_method": modification_method,
            "modification_result_tokens": modification_tokens,
            "multi_turn_result": multi_turn_result,
            "multi_turn_result_cost": multi_turn_cost,
            "multi_turn_result_detection_method": multi_turn_method,
            "multi_turn_result_tokens": multi_turn_tokens,
            "total_cost": total_cost,
            "total_tokens": total_token_usage,
            "sanity_check_failed": False,
            "warning_message": None
        }

        logger.info(f"Consolidated ConversationAnalyst checks result: {consolidated}")

        return consolidated
