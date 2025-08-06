from app.features.conversation.llm_responder import LLMResponder
from app.features.conversation.multi_turn import MultiTurn
from app.features.sanity_checks.sanity_checks_analyst import SanityChecksAnalyst
from app.utility.logging import get_logger
from app.config.features_config import ENABLE_MULTI_TURN, WARNING_MESSAGES, CHECKS_TO_RUN_MULTI_TURN

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
        # Run sanity checks first
        sanity_analyst = SanityChecksAnalyst(self.model)
        results = sanity_analyst.run_checks(prompt, conv_history, conv_history, checks_to_run=CHECKS_TO_RUN_MULTI_TURN)
        failed = next((k for k, v in results.items() if not v["passed"]), None)
        if failed:
            return {
                "continued_response": None,
                "modification_result": None,
                "multi_turn_result": None,
                "sanity_check_failed": True,
                "warning_message": WARNING_MESSAGES.get(failed, "Votre message n'est pas accepté.")
            }
        # Run Conversation methods
        continued_response = self.conversation.continue_conversation(prompt, conv_history)
        modification_result = self.conversation.detect_query_modification(prompt, conv_history)

        # Conditionally run MultiTurn analysis
        multi_turn_result = None
        if ENABLE_MULTI_TURN and self.multi_turn:
            multi_turn_result = self.multi_turn.analyze_subsequent_message(prompt, conv_history)

        # Consolidate all results
        consolidated = {
            "continued_response": continued_response,
            "modification_result": modification_result,
            "multi_turn_result": multi_turn_result,
            "sanity_check_failed": False,
            "warning_message": None
        }
        return consolidated
