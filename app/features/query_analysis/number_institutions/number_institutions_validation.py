from app.config.features_config import number_institutions_MIN, number_institutions_MAX

class NumberInstitutionsValidator:
    """
    Class for validating number_institutions values.
    It checks if the provided number_institutions is within the allowed range
    and provides a method to finalize the number_institutions value based on user input,
    detected values, and a default value.
    Attributes:
        min_number_institutions (int): Minimum allowed number_institutions value.
        max_number_institutions (int): Maximum allowed number_institutions value.   
    Methods:
        validate_number_institutions(number_institutions: int) -> bool:
            Validates if the number_institutions value is within the allowed range.
        finalize_number_institutions(user_number_institutions: int, detected_number_institutions: int, default_number_institutions: int = 3) -> int:
            Normalizes number_institutions value by choosing the most appropriate one.  
    """
    def __init__(self):
        self.min_number_institutions = number_institutions_MIN
        self.max_number_institutions = number_institutions_MAX

    def validate_number_institutions(self, number_institutions: int) -> bool:
        """
        Validates if the number_institutions value is within the allowed range.
        """
        return self.min_number_institutions <= number_institutions <= self.max_number_institutions

    def finalize_number_institutions(self, user_number_institutions: int, detected_number_institutions: int, default_number_institutions: int = 3) -> int:
        """
        Normalizes number_institutions value by choosing the most appropriate one.
        """
        # Safely cast detected_number_institutions and user_number_institutions to int if possible
        try:
            detected_number_institutions_int = int(detected_number_institutions)
        except (ValueError, TypeError):
            detected_number_institutions_int = 0
        try:
            user_number_institutions_int = int(user_number_institutions)
        except (ValueError, TypeError):
            user_number_institutions_int = 0
        if detected_number_institutions_int > 0 and self.validate_number_institutions(detected_number_institutions_int):
            return detected_number_institutions_int
        if self.validate_number_institutions(user_number_institutions_int):
            return user_number_institutions_int
        return default_number_institutions
