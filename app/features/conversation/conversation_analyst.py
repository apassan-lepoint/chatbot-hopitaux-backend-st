from app.features.conversation.llm_responder import LLMResponder
from app.features.conversation.multi_turn import MultiTurn
from app.utility.logging import get_logger

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
        self.multi_turn = MultiTurn(model)

    def run_all_conversation_checks(self, prompt: str, conv_history: list) -> dict:
        logger.debug(f"Running all conversation checks: prompt={prompt}, conv_history={conv_history}")
        """
        Runs all conversation-related checks and consolidates results into a dictionary with the following keys:
        - 'continued_response': Result of continuing the conversation.
        - 'modification_result': Result of detecting query modification.
        - 'multi_turn_result': Result of analyzing subsequent messages in a multi-turn conversation.
        """
        # Run Conversation methods
        continued_response = self.conversation.continue_conversation(prompt, conv_history)
        modification_result = self.conversation.detect_query_modification(prompt, conv_history)
        
        # Run MultiTurn analysis
        multi_turn_result = self.multi_turn.analyze_subsequent_message(prompt, conv_history)

        # Consolidate all results
        consolidated = {
            "continued_response": continued_response,
            "modification_result": modification_result,
            "multi_turn_result": multi_turn_result
        }
        return consolidated
