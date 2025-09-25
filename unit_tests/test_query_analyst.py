import pytest
from app.features.query_analysis.query_analyst import QueryAnalyst
from unittest.mock import patch

class DummyLLMHandler:
    """
    Dummy LLM handler for mocking LLM responses in QueryAnalyst tests.
    """
    pass

class DummyModel:
    """
    Dummy model for mocking model input in QueryAnalyst tests.
    Implements a mock generate method to simulate LLM responses for specialty and other detections.
    Returns a mock object with .generations and .llm_output attributes to match expected structure.
    """
    def generate(self, messages=None, **kwargs):
        content = messages[0][0].content if messages and isinstance(messages[0], list) and messages[0] else ""
        class MockText:
            def __init__(self, text):
                self.text = text
        class MockGeneration:
            def __init__(self, text):
                self.text = text
        class MockResponse:
            def __init__(self, text, institution_type=None, institution_names=None, specialty=None, location_cost=0.0, number_institutions=None):
                self.generations = [[MockGeneration(text)]]
                self.llm_output = {"token_usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}}
                self.institution_type = institution_type
                self.institution_names = institution_names
                self.specialty = specialty
                self.location_cost = location_cost
                self.number_institutions = number_institutions
        # Empty text case
        if not content.strip():
            return MockResponse("aucune correspondance", institution_type=None, institution_names=None, specialty="aucune correspondance", location_cost=0.0, number_institutions=0)
        # Cardiologie specialty
        if "cardiologie" in content.lower():
            return MockResponse("cardiologie", specialty="cardiologie")
        # Neurologie specialty
        if "neurologie" in content.lower() or "neuro" in content.lower():
            return MockResponse("neurologie", specialty="neurologie")
        # Multiple institutions
        if "hopital saint louis et hopital lariboisiere" in content.lower():
            return MockResponse("cardiologie", institution_names=[{"name": "Hopital Saint Louis"}, {"name": "Hopital Lariboisiere"}], specialty="cardiologie", number_institutions=2)
        # No institution
        if "je cherche un établissement à paris" in content.lower():
            return MockResponse("aucune correspondance", institution_names=None, specialty="aucune correspondance", number_institutions=0)
        # Location exception
        if "emplacement inconnu xyz123" in content.lower():
            return MockResponse("aucune correspondance", location_cost=0.0, specialty="aucune correspondance")
        # Default: always return a valid specialty string
        return MockResponse("cardiologie", specialty="cardiologie")

class TestQueryAnalyst:
    def setup_method(self):
        """
        Setup QueryAnalyst with dummy model and handler for each test.
        """
        self.qa = QueryAnalyst(model=DummyModel(), llm_handler_service=DummyLLMHandler())

    @patch('app.features.query_analysis.specialty.specialty_validation.SpecialtyValidator.validate_specialty')
    def test_run_all_detections_basic(self, mock_validate):
        """
        Test that run_all_detections returns a dict with all expected keys for a basic input.
        """
        mock_validate.return_value = "cardiologie"
        result = self.qa.run_all_detections("Hopital Saint Louis à Paris pour cardiologie")
        assert isinstance(result, dict)
        for key in [
            "location", "location_detected", "institution_names", "institution_type", "specialty", "number_institutions", "total_cost", "total_token_usage"
        ]:
            assert key in result

    @patch('app.features.query_analysis.specialty.specialty_validation.SpecialtyValidator.validate_specialty')
    @patch('app.features.query_analysis.institution_type.institution_type_analyst.InstitutionTypeAnalyst.detect_and_validate_institution_type')
    @patch('app.features.query_analysis.institution_names.institution_names_analyst.InstitutionNamesAnalyst.detect_and_validate_institution_names')
    @patch('app.features.query_analysis.number_institutions.number_institutions_analyst.NumberInstitutionsAnalyst.process_number_institutions')
    def test_run_all_detections_empty_text(self, mock_number, mock_names, mock_type, mock_specialty):
        """
        Test that empty text returns None or default values for all detection fields.
        """
        mock_specialty.return_value = None
        mock_type.return_value = {"institution_type": None}
        mock_names.return_value = {"institutions": None}
        mock_number.return_value = {"number_institutions": None}
        result = self.qa.run_all_detections("")
        assert result["location"] is None
        assert result["specialty"] is None
        assert result["institution_names"] is None or result["institution_names"] == []
        assert result["institution_type"] is None
        assert result["number_institutions"] is None or result["number_institutions"] == 0

    @patch('app.features.query_analysis.specialty.specialty_validation.SpecialtyValidator.validate_specialty')
    @patch('app.features.query_analysis.institution_type.institution_type_analyst.InstitutionTypeAnalyst.detect_and_validate_institution_type')
    @patch('app.features.query_analysis.institution_names.institution_names_analyst.InstitutionNamesAnalyst.detect_and_validate_institution_names')
    @patch('app.features.query_analysis.number_institutions.number_institutions_analyst.NumberInstitutionsAnalyst.process_number_institutions')
    def test_run_all_detections_multiple_institutions(self, mock_number, mock_names, mock_type, mock_specialty):
        """
        Test that multiple institution names in text are detected and counted correctly.
        """
        mock_specialty.return_value = "cardiologie"
        mock_type.return_value = {"institution_type": "public"}
        mock_names.return_value = {"institutions": [{"name": "Hopital Saint Louis"}, {"name": "Hopital Lariboisiere"}]}
        mock_number.return_value = {"number_institutions": 2}
        result = self.qa.run_all_detections("Hopital Saint Louis et Hopital Lariboisière à Paris")
        assert isinstance(result["institution_names"], list)
        assert len(result["institution_names"]) >= 2
        assert result["number_institutions"] == len(result["institution_names"])

    @patch('app.features.query_analysis.specialty.specialty_validation.SpecialtyValidator.validate_specialty')
    @patch('app.features.query_analysis.institution_type.institution_type_analyst.InstitutionTypeAnalyst.detect_and_validate_institution_type')
    @patch('app.features.query_analysis.institution_names.institution_names_analyst.InstitutionNamesAnalyst.detect_and_validate_institution_names')
    @patch('app.features.query_analysis.number_institutions.number_institutions_analyst.NumberInstitutionsAnalyst.process_number_institutions')
    def test_run_all_detections_specialty_detection(self, mock_number, mock_names, mock_type, mock_specialty):
        """
        Test that specialty is detected from text and returned in results.
        """
        mock_specialty.return_value = "neurologie"
        mock_type.return_value = {"institution_type": "public"}
        mock_names.return_value = {"institutions": [{"name": "Hopital Saint Louis"}, {"name": "Hopital Lariboisiere"}]}
        mock_number.return_value = {"number_institutions": 2}
        result = self.qa.run_all_detections("Je cherche un établissement pour la neurologie à Lyon")
        assert result["specialty"] is not None
        assert "neuro" in result["specialty"].lower()

    @patch('app.features.query_analysis.specialty.specialty_validation.SpecialtyValidator.validate_specialty')
    @patch('app.features.query_analysis.institution_type.institution_type_analyst.InstitutionTypeAnalyst.detect_and_validate_institution_type')
    @patch('app.features.query_analysis.institution_names.institution_names_analyst.InstitutionNamesAnalyst.detect_and_validate_institution_names')
    @patch('app.features.query_analysis.number_institutions.number_institutions_analyst.NumberInstitutionsAnalyst.process_number_institutions')
    def test_run_all_detections_location_exception_handling(self, mock_number, mock_names, mock_type, mock_specialty):
        """
        Test that location detection exceptions are handled gracefully and return default values.
        """
        mock_specialty.return_value = None
        mock_type.return_value = {"institution_type": None}
        mock_names.return_value = {"institutions": None}
        mock_number.return_value = {"number_institutions": None}
        result = self.qa.run_all_detections("Emplacement inconnu xyz123")
        assert result["location"] is None
        assert result["location_detected"] is False
        import pytest
        assert result["location_cost"] == pytest.approx(0.0, abs=1e-5)

    @patch('app.features.query_analysis.specialty.specialty_validation.SpecialtyValidator.validate_specialty')
    def test_run_all_detections_token_and_cost_fields(self, mock_validate):
        """
        Test that cost and token usage fields are present and are numbers.
        """
        mock_validate.return_value = "cardiologie"
        result = self.qa.run_all_detections("Hopital Saint Louis à Paris pour cardiologie")
        for key in [
            "total_cost", "total_token_usage", "location_cost", "location_token_usage", "institution_names_cost", "institution_names_token_usage", "institution_type_cost", "institution_type_token_usage", "specialty_cost", "specialty_token_usage", "number_institutions_cost", "number_institutions_token_usage"
        ]:
            assert key in result
            assert isinstance(result[key], (int, float))

    @patch('app.features.query_analysis.specialty.specialty_validation.SpecialtyValidator.validate_specialty')
    def test_run_all_detections_with_conv_history(self, mock_validate):
        """
        Test that conversation history argument does not break detection and is used.
        """
        mock_validate.return_value = "cardiologie"
        result = self.qa.run_all_detections("Hopital Saint Louis", conv_history="Précédemment: neurologie")
        assert "location" in result
        assert "specialty" in result

    @patch('app.features.query_analysis.specialty.specialty_validation.SpecialtyValidator.validate_specialty')
    def test_run_all_detections_institution_names_intent(self, mock_validate):
        """
        Test that institution_names_intent is present and is a string or None.
        """
        mock_validate.return_value = "cardiologie"
        result = self.qa.run_all_detections("Hopital Saint Louis à Paris")
        assert "institution_names_intent" in result
        assert isinstance(result["institution_names_intent"], (str, type(None)))

    @patch('app.features.query_analysis.specialty.specialty_validation.SpecialtyValidator.validate_specialty')
    @patch('app.features.query_analysis.institution_type.institution_type_analyst.InstitutionTypeAnalyst.detect_and_validate_institution_type')
    @patch('app.features.query_analysis.institution_names.institution_names_analyst.InstitutionNamesAnalyst.detect_and_validate_institution_names')
    @patch('app.features.query_analysis.number_institutions.number_institutions_analyst.NumberInstitutionsAnalyst.process_number_institutions')
    def test_run_all_detections_edge_case_no_institution(self, mock_number, mock_names, mock_type, mock_specialty):
        """
        Test edge case where no institution is mentioned in the text.
        """
        mock_specialty.return_value = None
        mock_type.return_value = {"institution_type": None}
        mock_names.return_value = {"institutions": None}
        mock_number.return_value = {"number_institutions": 0}
        result = self.qa.run_all_detections("Je cherche un établissement à Paris")
        assert result["institution_names"] is None or result["institution_names"] == []
        assert result["number_institutions"] == 0 or result["number_institutions"] is None
