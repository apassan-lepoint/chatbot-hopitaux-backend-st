from .snowflake_connector import get_snowflake_connection

def run_sql(sql: str):
    conn = get_snowflake_connection()
    cursor = conn.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

