import snowflake.connector
import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

def get_snowflake_connection():
    """
    Establish and return a connection to the Snowflake database using credentials and configuration loaded from environment variables.

    Returns:
        snowflake.connector.connection.SnowflakeConnection: An active Snowflake connection object.

    Raises:
        snowflake.connector.errors.Error: If the connection fails due to invalid credentials or configuration.
    """

    return snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA")
    )
