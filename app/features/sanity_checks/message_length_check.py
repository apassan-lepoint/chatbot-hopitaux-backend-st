from app.config.features_config import MAX_LENGTH, MESSAGE_LENGTH_RESPONSE

class MessageLengthCheckException(Exception):
    """
    Exception raised when a message exceeds the maximum allowed length.
    """
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
            raise MessageLengthCheckException(MESSAGE_LENGTH_RESPONSE)
