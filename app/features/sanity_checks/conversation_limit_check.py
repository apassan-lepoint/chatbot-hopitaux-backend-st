from app.config.features_config import MAX_MESSAGES, MESSAGE_LIMIT_REACHED_RESPONSE

class ConversationLimitCheckException(Exception):
    """
    Exception raised when the conversation exceeds the maximum number of messages allowed.
    """
    pass
class ConversationLimitChecker:
    """
    Class to check if a conversation has reached the maximum number of messages allowed.
    It raises a ConversationLimitCheckException if the limit is exceeded.
    """
    def __init__(self, max_messages=MAX_MESSAGES):
        self.max_messages = max_messages

    def check(self, conversation):
        """
        Checks if the conversation has reached the maximum number of messages allowed.
        """
        if len(conversation) >= self.max_messages:
            raise ConversationLimitCheckException(MESSAGE_LIMIT_REACHED_RESPONSE)