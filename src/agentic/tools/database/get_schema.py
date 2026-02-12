import os
from RAW.modals import Tool
from RAW.modals.tools import ToolParam
from src.utils import logger
from src.utils.database import get_db_connection

def get_schema(table_names: list[str] = None) -> str:
    """
    Fetches the schema (table name, column name, data type) for the specified tables
    from the target database. If no tables are specified, fetches all public tables.
    """
    try:
        with get_db_connection() as conn:
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

get_schema_tool = Tool(
    name="get_schema",
    description="Fetches schema information (tables, columns, datatypes) from the target database. Can filter by a list of table names.",
    function=get_schema,
    parameters=[
        ToolParam(
            name="table_names",
            type="array",
            description="Optional list of table names to fetch schema for. If omitted, returns all public tables.",
            items={"type": "string"},
            required=False
        )
    ]
)
