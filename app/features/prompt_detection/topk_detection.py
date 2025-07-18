"""
Module for detecting the number of establishments (top-k) requested by users.

This module handles the detection of how many hospital/clinic results the user wants
to see, with support for conversation history context.
"""

from app.utility.logging import get_logger
from app.utility.llm_helpers import invoke_llm_with_error_handling
from app.utility.wrappers import prompt_formatting, parse_llm_response

logger = get_logger(__name__)


class TopKDetector:
    """
    Service for detecting the number of establishments (top-k) requested by users.
    Handles detection from user messages with conversation context support.
    
    """
    
    def __init__(self, model):
        """
        Initialize the TopKDetector.
        
        Args:
            model: The language model used for detection
        """
        self.model = model
        self._default_topk = 3
        self._max_topk = 50
        self._min_topk = 1
        # TODO make these constants in config file 
    
    
    def detect_topk(self, prompt: str, conv_history: str = "") -> int:
        """
        Detects the top-k results from the given prompt using the LLM.
        Returns integer for top-k or 0 if not mentioned.
        
        Args:
            prompt: The message to analyze
            conv_history: Optional conversation history for context
            
        Returns:
            int: Number of establishments requested (1-50) or 0 if not mentioned
        """
        try:
            logger.debug(f"Detecting top-k from prompt: {prompt[:50]}...")
            
            formatted_prompt = prompt_formatting("detect_topk_prompt", prompt, conv_history)
            raw_response = invoke_llm_with_error_handling(self.model, formatted_prompt, "detect_topk")
            topk = parse_llm_response(raw_response, "numeric", 0)
            
            # Validate range
            if self._min_topk <= topk <= self._max_topk:
                logger.debug(f"Valid top-k detected: {topk}")
                return topk
            else:
                logger.debug(f"Top-k out of range or not mentioned: {topk}")
                return 0
                
        except Exception as e:
            logger.error(f"Error detecting top-k: {e}")
            return 0
    

    def detect_topk_with_fallback(self, prompt: str, conv_history: str = "", as_string: bool = False) -> int | str:
        """
        Detects top-k with fallback to default value or string.
        If as_string=True, returns string or 'non mentionné'.
        """
        detected_topk = self.detect_topk(prompt, conv_history)
        if as_string:
            return str(detected_topk) if detected_topk > 0 else 'non mentionné'
        return detected_topk if detected_topk > 0 else self._default_topk

    def validate_topk(self, topk: int) -> bool:
        return self._min_topk <= topk <= self._max_topk

    def normalize_topk_for_query(self, user_topk: int, detected_topk: int) -> int:
        """Normalizes top-k value by choosing the most appropriate one."""
        if detected_topk > 0 and self.validate_topk(detected_topk):
            return detected_topk
        if self.validate_topk(user_topk):
            return user_topk
        return self._default_topk



# Utility functions for backward compatibility (optional, can be removed if not used)
def detect_topk_from_prompt(model, prompt: str, conv_history: str = "") -> int:
    return TopKDetector(model).detect_topk(prompt, conv_history)

def get_topk_with_default(model, prompt: str, conv_history: str = "", default: int = 3) -> int:
    detector = TopKDetector(model)
    detector._default_topk = default
    return detector.detect_topk_with_fallback(prompt, conv_history)