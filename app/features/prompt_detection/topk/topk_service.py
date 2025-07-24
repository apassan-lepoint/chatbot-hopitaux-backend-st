"""
Service for orchestrating top-k detection and validation.
"""
from .topk_detection import TopKDetector
from .topk_validation import TopKValidation

class TopKService:
    """
    Service to detect and validate the number of establishments (top-k) requested by users.
    """
    def __init__(self, model=None, min_topk=1, max_topk=50, default_topk=3):
        self.detector = TopKDetector(model)
        self.validator = TopKValidation(min_topk, max_topk)
        self.default_topk = default_topk

    def process_topk(self, prompt: str, conv_history: str = "", user_topk: int = None) -> int:
        """
        Detects and validates the top-k value from the prompt.
        Args:
            prompt (str): The message to analyze
            conv_history (str, optional): Conversation history for context
            user_topk (int, optional): User-provided top-k value
        Returns:
            int: Final validated top-k value
        """
        detected_topk = self.detector.detect_topk(prompt, conv_history)
        user_topk = user_topk if user_topk is not None else 0
        return self.validator.finalize_topk(user_topk, detected_topk, self.default_topk)
