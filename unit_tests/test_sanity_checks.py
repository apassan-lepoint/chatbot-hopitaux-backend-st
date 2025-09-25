import pytest
from app.features.sanity_checks.conversation_limit_check import ConversationLimitChecker
from app.features.sanity_checks.message_length_check import MessageLengthChecker
from app.features.sanity_checks.message_pertinence_check import MessagePertinenceChecker
from app.features.sanity_checks.sanity_checks_analyst import SanityChecksAnalyst

class DummyLLMHandler:
    class model:
        @staticmethod
        def generate(messages):
            class Response:
                generations = [[type('Gen', (), {'text': '1'})]]
                llm_output = {"token_usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}
            return Response()

class TestSanityChecks:

    def test_conversation_limit_checker(self):
        """
        Test ConversationLimitChecker for normal and edge cases.
        """
        checker = ConversationLimitChecker(max_messages=3)
        # Under limit
        assert checker.check([1,2,3])["passed"] is True
        # Over limit
        result = checker.check([1,2,3,4])
        assert result["passed"] is False and "error" in result
        # Empty conversation
        assert checker.check([])["passed"] is True

    def test_message_length_checker(self):
        """
        Test MessageLengthChecker for normal, over, and empty cases.
        """
        checker = MessageLengthChecker(max_length=5)
        # Under limit
        assert checker.check("12345")["passed"] is True
        # Over limit
        result = checker.check("123456")
        assert result["passed"] is False and "error" in result
        # Empty message
        assert checker.check("")["passed"] is True

    def test_message_pertinence_checker(self):
        """
        Test MessagePertinenceChecker for typical and edge cases using dummy LLM handler.
        """
        checker = MessagePertinenceChecker(DummyLLMHandler(), pertinent_chatbot_use_case=True)
        # Medically pertinent (simulated)
        result = checker.check("valid medical question", "history")
        assert result["passed"] is True
        # Not medically pertinent (simulate by changing dummy response if needed)
        # Methodology question (simulate by changing dummy response if needed)

    def test_sanity_checks_analyst(self):
        """
        Test SanityChecksAnalyst for running all checks and edge cases.
        """
        analyst = SanityChecksAnalyst(DummyLLMHandler(), max_messages=3, max_length=5, pertinent_chatbot_use_case=True)
        # All checks pass
        result = analyst.run_checks("12345", [1,2,3], "history")
        assert result["passed"] is True
        # Message length fails (should raise Exception)
        with pytest.raises(Exception) as excinfo:
            analyst.run_checks("123456", [1,2,3], "history")
        assert "message" in str(excinfo.value).lower() or "long" in str(excinfo.value).lower()
        # Conversation limit fails (should raise Exception)
        with pytest.raises(Exception) as excinfo:
            analyst.run_checks("12345", [1,2,3,4], "history")
        assert "conversation" in str(excinfo.value).lower() or "limit" in str(excinfo.value).lower()

