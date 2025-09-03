from app.config.features_config import MAX_LENGTH, ERROR_MESSAGES

class MessageLengthCheckException(Exception):
    pass

class MessageLengthChecker:
    """
    Class to check if a message exceeds the maximum allowed length.
    """
    def __init__(self, max_length=MAX_LENGTH):
        self.max_length = max_length

    def check(self, message):
        """
        Checks if the message exceeds the maximum allowed length.
        """
        if len(message) > self.max_length:
            return {"passed": False, "error": f"Message exceeds maximum length of {self.max_length} characters.", "detection_method": "rule", "warning": ERROR_MESSAGES.get("message_length", "")}
        else:
            return {"passed": True}
