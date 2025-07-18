from config.features_config import MAX_LENGTH

class MessageLengthCheckException(Exception):
    pass

class MessageLengthChecker:
    def __init__(self, max_length=MAX_LENGTH):
        self.max_length = max_length

    def check(self, message):
        """
        Checks if the message exceeds the maximum allowed length.

        Args:
            message (str): The message to check.

        Raises:
            MessageLengthCheckException: If the message is too long.
        """
        if len(message) > self.max_length:
            raise MessageLengthCheckException("Votre message est trop long. Merci de reformuler.")
