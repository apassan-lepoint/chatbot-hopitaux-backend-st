import pytest
from unittest.mock import patch, MagicMock
from app.services.pipeline_orchestrator_service import PipelineOrchestratorService
import pandas as pd


class TestPipelineOrchestratorService:
    def setup_method(self):
        """
        Setup PipelineOrchestratorService with mocked dependencies for each test.
        """
        with patch('app.services.pipeline_orchestrator_service.DataProcessorService', autospec=True):
            self.service = PipelineOrchestratorService()
            self.service.data_processor = MagicMock()

    def test_reset_attributes(self):
        """
        Test that reset_attributes sets all relevant attributes to None.
        """
        self.service.specialty = 'cardio'
        self.service.institution_type = 'public'
        self.service.location = {'city': 'Paris'}
        self.service.reset_attributes()
        assert self.service.specialty is None
        assert self.service.institution_type is None
        assert self.service.location is None

    def test_extract_query_parameters(self):
        """
        Test that extract_query_parameters returns a dict and sets query_analyst_results.
        """
        mock_llm_handler = MagicMock()
        self.service.data_processor.llm_handler_service = mock_llm_handler
        with patch('app.services.pipeline_orchestrator_service.QueryAnalyst', autospec=True) as mock_analyst:
            mock_instance = mock_analyst.return_value
            mock_instance.run_all_detections.return_value = {'specialty': 'cardio', 'location': 'Paris'}
            result = self.service.extract_query_parameters('prompt')
            assert isinstance(result, dict)
            assert result['specialty'] == 'cardio'
            assert self.service.query_analyst_results == result

    def test_generate_response_success(self):
        """
        Test that generate_response returns a tuple (response, links) on success.
        """
        self.service.reset_attributes = MagicMock()
        self.service._run_sanity_checks = MagicMock(return_value=None)
        self.service.extract_query_parameters = MagicMock(return_value={'specialty': 'cardio'})
        self.service.data_processor.load_snowflake_dataframe.return_value = MagicMock()
        self.service._handle_response_generation_failure = MagicMock()
        # Properly mock process_other_query to return two empty DataFrames
        self.service.data_processor.process_other_query = MagicMock(return_value=(pd.DataFrame(), pd.DataFrame()))
        response, links = self.service.generate_response('prompt')
        assert isinstance(response, str) or response is None
        assert isinstance(links, list)

    def test_generate_response_data_load_failure(self):
        """
        Test edge case: generate_response handles snowflake data load failure.
        """
        self.service.reset_attributes = MagicMock()
        self.service.data_processor.load_snowflake_dataframe.side_effect = Exception('DB error')
        self.service._handle_response_generation_failure = MagicMock(return_value=('error', []))
        response, links = self.service.generate_response('prompt')
        assert response == 'error'
        assert links == []
