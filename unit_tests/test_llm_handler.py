import pytest
from unittest.mock import patch, MagicMock
from app.services.llm_handler_service import LLMHandlerService


class TestLLMHandlerService:
    def setup_method(self):
        """
        Setup LLMHandlerService with mocked model and conversation manager for each test.
        """
        with patch('app.services.llm_handler_service.ChatOpenAI', autospec=True):
            with patch('app.services.llm_handler_service.ConversationAnalyst', autospec=True):
                self.service = LLMHandlerService()
                self.service.model = MagicMock()
                self.service.conversation_manager = MagicMock()
                self.mock_analyst = self.service.conversation_manager

    def test_init_model(self):
        """
        Test that init_model returns a ChatOpenAI instance (mocked).
        """
        with patch('app.services.llm_handler_service.ChatOpenAI', autospec=True) as mock_model:
            model = self.service.init_model()
            assert model is not None
            assert isinstance(model, MagicMock)

    def test_run_conversation_checks(self):
        """
        Test that run_conversation_checks returns a dict of results.
        """
        self.mock_analyst.run_all_conversation_checks.return_value = {'check': 'ok'}
        result = self.service.run_conversation_checks('prompt', ['history'])
        assert isinstance(result, dict)
        assert result['check'] == 'ok'

    def test_rewrite_query_merge(self):
        """
        Test that rewrite_query_merge returns a string (mocked).
        """
        self.mock_analyst.conversation.rewrite_query_merge.return_value = 'merged_query'
        result = self.service.rewrite_query_merge('prompt', 'history')
        assert isinstance(result, str)
        assert result == 'merged_query'

    def test_rewrite_query_add(self):
        """
        Test that rewrite_query_add returns a string (mocked).
        """
        self.mock_analyst.conversation.rewrite_query_add.return_value = 'added_query'
        result = self.service.rewrite_query_add('prompt', 'history')
        assert isinstance(result, str)
        assert result == 'added_query'

    def test_init_model_no_api_key(self):
        """
        Test edge case: init_model with no API key in environment.
        """
        with patch('os.getenv', return_value=None):
            with patch('app.services.llm_handler_service.ChatOpenAI', autospec=True):
                model = self.service.init_model()
                assert model is not None
                assert isinstance(model, MagicMock)
