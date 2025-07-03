"""
Database query utilities.

This file provides functions for querying hospital and ranking data from the database,
    abstracting SQL logic for use throughout the application.
"""

from .snowflake_connector import get_snowflake_connection

def run_sql(sql: str):
    """
    Execute a given SQL query using a Snowflake database connection.
    The function opens a new connection for each call and closes it after execution.
    
    Args:
        sql (str): The SQL query to execute.
    
    Returns:
        list: The result of the query as a list of rows (tuples).
    
    Raises:
        Any exceptions raised by the Snowflake connector during connection or execution.
    """
    # Get a new Snowflake database connection 
    conn_sf = get_snowflake_connection()
    
    # Create a cursor object to execute the SQL query
    cursor = conn_sf.cursor()
    
    # Execute the provided SQL query
    cursor.execute(sql)
    
    # Fetch all results from the executed query
    result = cursor.fetchall()
    
    # Close the cursor and connection to free resources
    cursor.close()
    
    # Close the connection to the Snowflake database
    conn_sf.close()
    
    return result
