"""
Manager to consolidate results from Conversation and MultiTurn classes.
"""
from app.features.conversation.llm_responder import LLMResponder
from app.features.conversation.multi_turn import MultiTurn

class ConversationManager:
    def __init__(self, model):
        self.model = model
        self.conversation = LLMResponder(model)
        self.multi_turn = MultiTurn(model)

    def run_all_conversation_checks(self, prompt: str, conv_history: list) -> dict:
        """
        Runs all conversation-related checks and consolidates results into a dictionary.
        Args:
            prompt (str): User's input message.
            conv_history (list): Conversation history.
        Returns:
            dict: Consolidated results from Conversation and MultiTurn.
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
