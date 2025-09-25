import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from app.snowflake_db import snowflake_connector, snowflake_query

class TestSnowflakeDB:
    def test_get_snowflake_connection_success(self):
        """
        Test that get_snowflake_connection returns a connection object.
        This test mocks the connector to avoid real DB calls.
        """
        with patch('app.snowflake_db.snowflake_connector.snowflake.connector.connect') as mock_connect:
            mock_connect.return_value = MagicMock(name='SnowflakeConnection')
            conn = snowflake_connector.get_snowflake_connection()
            assert conn is not None
            assert hasattr(conn, 'close')

    def test_get_snowflake_connection_env_missing(self):
        """
        Test that get_snowflake_connection raises if env vars are missing.
        """
        with patch('os.getenv', return_value=None):
            with patch('app.snowflake_db.snowflake_connector.snowflake.connector.connect') as mock_connect:
                mock_connect.side_effect = Exception('Missing env')
                with pytest.raises(Exception):
                    snowflake_connector.get_snowflake_connection()

    def test_run_sql_success(self):
        """
        Test that run_sql executes SQL and returns results and columns.
        This test mocks the connection and cursor, including all methods and attributes, to prevent real DB calls.
        """
        mock_cursor = MagicMock()
        mock_cursor.execute.return_value = None
        mock_cursor.fetchall.return_value = [(1, 'A'), (2, 'B')]
        mock_cursor.description = [('id',), ('name',)]
        mock_conn = MagicMock()
        # Patch the connection's cursor method to always return our mock_cursor
        with patch('app.snowflake_db.snowflake_connector.snowflake.connector.connect', return_value=mock_conn):
            mock_conn.cursor.return_value = mock_cursor
            with patch('app.snowflake_db.snowflake_connector.get_snowflake_connection', return_value=mock_conn):
                result, columns = snowflake_query.run_sql('SELECT * FROM test')
                assert result == [(1, 'A'), (2, 'B')]
                assert columns == ['id', 'name']

    def test_run_sql_error(self):
        """
        Test that run_sql raises on SQL execution error.
        """
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception('SQL error')
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        with patch('app.snowflake_db.snowflake_connector.get_snowflake_connection', return_value=mock_conn):
            with pytest.raises(Exception):
                snowflake_query.run_sql('BAD SQL')

    def test_convert_snowflake_to_pandas_df_success(self):
        """
        Test that convert_snowflake_to_pandas_df returns a DataFrame with correct columns and data.
        """
        with patch('app.snowflake_db.snowflake_query.run_sql', return_value=([(1, 'A'), (2, 'B')], ['id', 'name'])):
            df = snowflake_query.convert_snowflake_to_pandas_df('SELECT * FROM test')
            assert isinstance(df, pd.DataFrame)
            assert list(df.columns) == ['id', 'name']
            assert len(df) == 2

    def test_convert_snowflake_to_pandas_df_empty(self):
        """
        Test edge case where SQL returns no rows.
        """
        with patch('app.snowflake_db.snowflake_query.run_sql', return_value=([], ['id', 'name'])):
            df = snowflake_query.convert_snowflake_to_pandas_df('SELECT * FROM test')
            assert isinstance(df, pd.DataFrame)
            assert df.empty
