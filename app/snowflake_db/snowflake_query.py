"""
query.py
---------------------------------
This file provides functions for querying the Snowflake database.
"""

import pandas as pd
from .snowflake_connector import get_snowflake_connection


def run_sql(sql: str):
    """
    Execute a given SQL query using a Snowflake database connection.
    The function opens a new connection for each call and closes it after execution.
    """
    # Get a new Snowflake database connection 
    conn_sf = get_snowflake_connection()
    # Create a cursor object to execute the SQL query
    cursor = conn_sf.cursor()
    # Execute the provided SQL query
    cursor.execute(sql)
    # Fetch all results from the executed query
    result = cursor.fetchall()
    # Fetch the column names from the cursor description
    columns = [desc[0] for desc in cursor.description]
    # Close the cursor and connection to free resources
    cursor.close()
    # Close the connection to the Snowflake database
    conn_sf.close()
    return result, columns

def convert_snowflake_to_pandas_df(sql_query: str) -> pd.DataFrame:
    """
    Convert the result of a SQL query executed on Snowflake into a Pandas DataFrame.
    """
    data, columns = run_sql(sql_query)
    pandas_df = pd.DataFrame(data, columns=columns)
    return pandas_df