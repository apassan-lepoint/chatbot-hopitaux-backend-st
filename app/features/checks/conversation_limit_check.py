from app.configfeatures_config import MAX_MESSAGES

class ConversationLimitCheckException(Exception):
    pass

class ConversationLimitChecker:
    def __init__(self, max_messages=MAX_MESSAGES):
        self.max_messages = max_messages

    def check(self, conversation):
        """
        Checks if the conversation has reached the maximum number of messages allowed.

        Args:
            conversation (list): The conversation history.

        Raises:
            ConversationLimitCheckException: If the limit is reached.
        """
        if len(conversation) >= self.max_messages:
            raise ConversationLimitCheckException("La limite de messages a été atteinte. La conversation va redémarrer.")