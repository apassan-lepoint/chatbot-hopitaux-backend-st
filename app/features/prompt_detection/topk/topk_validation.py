"""
Module for validating the number of establishments (top-k) detected from user queries.

This module provides validation logic for top-k values, ensuring they are within acceptable bounds.
"""
from app.config.features_config import TOPK_MIN, TOPK_MAX

class TopKValidation:
    """
    Class for validating top-k values.
    """
    def __init__(self):
        self.min_topk = TOPK_MIN
        self.max_topk = TOPK_MAX

    def validate_topk(self, topk: int) -> bool:
        """
        Validates if the topk value is within the allowed range.
        Args:
            topk (int): The top-k value to validate
        Returns:
            bool: True if valid, False otherwise
        """
        return self.min_topk <= topk <= self.max_topk

    def finalize_topk(self, user_topk: int, detected_topk: int, default_topk: int = 3) -> int:
        """
        Normalizes top-k value by choosing the most appropriate one.
        Args:
            user_topk (int): User-provided top-k
            detected_topk (int): Detected top-k
            default_topk (int): Default top-k value
        Returns:
            int: Normalized top-k value
        """
        # Safely cast detected_topk and user_topk to int if possible
        try:
            detected_topk_int = int(detected_topk)
        except (ValueError, TypeError):
            detected_topk_int = 0
        try:
            user_topk_int = int(user_topk)
        except (ValueError, TypeError):
            user_topk_int = 0
        if detected_topk_int > 0 and self.validate_topk(detected_topk_int):
            return detected_topk_int
        if self.validate_topk(user_topk_int):
            return user_topk_int
        return default_topk
