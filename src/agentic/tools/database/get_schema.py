import os
import psycopg2
from dotenv import load_dotenv
from RAW.modals import Tool
from RAW.modals.tools import ToolParam
from src.utils import logger

load_dotenv()

def get_db_connection():
    try:
        return psycopg2.connect(
            host=os.getenv("TARGET_DB_HOST", "localhost"),
            port=int(os.getenv("TARGET_DB_PORT", 5432)),
            dbname=os.getenv("TARGET_DB_NAME", "postgres"),
            user=os.getenv("TARGET_DB_USER", "postgres"),
            password=os.getenv("TARGET_DB_PASS", "postgres")
        )
    except Exception as e:
        logger.error(f"Failed to connect to target database: {e}")
        raise e

def get_schema(table_names: list[str] = None) -> str:
    """
    Fetches the schema (table name, column name, data type) for the specified tables
    from the target database. If no tables are specified, fetches all public tables.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if table_names:
            query = """
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = ANY(%s)
                ORDER BY table_name, ordinal_position;
            """
            cursor.execute(query, (table_names,))
        else:
            query = """
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position;
            """
            cursor.execute(query)

        rows = cursor.fetchall()
        
        if not rows:
            return "No schema found or no tables matched."

        schema_dict = {}
        for table, column, dtype in rows:
            schema_dict.setdefault(table, []).append(f"{column} ({dtype})")

        output_lines = []
        for table, columns in schema_dict.items():
            output_lines.append(f"Table: {table}")
            for col in columns:
                output_lines.append(f"  - {col}")
            output_lines.append("") # Empty line between tables

        return "\n".join(output_lines)

    except Exception as e:
        error_msg = f"Error fetching schema: {str(e)}"
        logger.error(error_msg)
        return error_msg
    finally:
        if conn:
            conn.close()

get_schema_tool = Tool(
    name="get_database_schema",
    description="Fetches schema information (tables, columns, datatypes) from the target database. Can filter by a list of table names.",
    function=get_schema,
    parameters=[
        ToolParam(
            name="table_names",
            type="array",
            description="Optional list of table names to fetch schema for. If omitted, returns all public tables.",
            required=False
        )
    ]
)
