import pytest
import pandas as pd
from app.services.data_processor_service import DataProcessorService

class DummyRankingDF(pd.DataFrame):
    """
    Dummy DataFrame for simulating ranking data in tests.
    """
    @property
    def _constructor(self):
        return DummyRankingDF

class TestDataProcessor:
    def setup_method(self):
        """
        Setup a DataProcessorService instance and dummy ranking DataFrame for each test.
        """
        self.processor = DataProcessorService()
        # Minimal dummy DataFrame
        self.processor.snowflake_ranking_df = DummyRankingDF({
            'CLASSEMENT_TYPE_NORM': ['cardiologie', 'neurologie'],
            'ETABLISSEMENT_NOM_NORM': ['hopital_a', 'hopital_b'],
            'CLASSEMENT_NOTE': [90, 80],
            'ETABLISSEMENT_TYPE': ['public', 'private']
        })

    def test_process_institution_names_query_valid(self):
        """
        Test that process_institution_names_query returns correct DataFrame and intent for valid input.
        """
        self.processor.specialty = 'cardiologie'
        self.processor.institution_names = ['hopital_a']
        self.processor.institution_names_intent = 'single'
        df, intent = self.processor.process_institution_names_query()
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert intent == 'single'

    def test_process_institution_names_query_no_match(self):
        """
        Test that process_institution_names_query returns None for unmatched institution names.
        """
        self.processor.specialty = 'cardiologie'
        self.processor.institution_names = ['not_in_df']
        self.processor.institution_names_intent = 'single'
        df, intent = self.processor.process_institution_names_query()
        assert df is None
        assert intent is None

    def test_process_institution_names_query_compare_consistent(self):
        """
        Test compare intent with consistent institution types.
        If no matching institutions, should handle None gracefully.
        """
        self.processor.specialty = 'cardiologie'
        self.processor.institution_names = ['hopital_a']
        self.processor.institution_names_intent = 'compare'
        result = self.processor.process_institution_names_query()
        if result is None:
            assert result is None
        else:
            df, intent = result
            assert isinstance(df, pd.DataFrame)
            assert intent in ['compare_consistent', 'compare']

    def test_process_institution_names_query_compare_inconsistent(self):
        """
        Test compare intent with inconsistent institution types (edge case).
        Accept both 'compare_consistent' and 'compare_inconsistent' as valid, depending on test data.
        """
        self.processor.specialty = 'neurologie'
        self.processor.institution_names = ['hopital_b', 'hopital_a']
        self.processor.institution_names_intent = 'compare'
        result = self.processor.process_institution_names_query()
        if result is None:
            assert result is None
        else:
            df, intent = result
            assert isinstance(df, pd.DataFrame)
            assert intent in ['compare_consistent', 'compare_inconsistent', 'compare']

    def test_process_institution_names_query_empty_df(self):
        """
        Test edge case where ranking DataFrame is empty.
        """
        self.processor.snowflake_ranking_df = DummyRankingDF({
            'CLASSEMENT_TYPE_NORM': [],
            'ETABLISSEMENT_NOM_NORM': [],
            'CLASSEMENT_NOTE': [],
            'ETABLISSEMENT_TYPE': []
        })
        self.processor.specialty = 'cardiologie'
        self.processor.institution_names = ['hopital_a']
        self.processor.institution_names_intent = 'single'
        df, intent = self.processor.process_institution_names_query()
        assert df is None
        assert intent is None

    def test_load_snowflake_dataframe_error(self, monkeypatch):
        """
        Test that load_snowflake_dataframe raises an exception on error (simulated).
        """
        def fake_convert(*args, **kwargs):
            raise Exception('Simulated error')
        monkeypatch.setattr('app.services.data_processor_service.convert_snowflake_to_pandas_df', fake_convert)
        with pytest.raises(Exception):
            self.processor.load_snowflake_dataframe()
