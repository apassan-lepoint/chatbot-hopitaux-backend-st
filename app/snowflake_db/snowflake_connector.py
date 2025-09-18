"""
snowflake_connector.py
---------------------------------
This file contains utilities for connecting to the Snowflake database.  
"""

import snowflake.connector
import os
from dotenv import load_dotenv


# Load environment variables from a .env file
load_dotenv()

def get_snowflake_connection():
    """
    Establish and return a connection to the Snowflake database using credentials and configuration loaded from environment variables.
    Returns:
        snowflake.connector.SnowflakeConnection: A connection object to the Snowflake database. 
    """
    return snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA")
    )
