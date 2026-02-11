import os
import json
import base64
import pandas as pd
from io import BytesIO
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import AsyncGenerator, Dict, Any

from RAW.modals import Tool
from RAW.modals.tools import ToolParam
from src.utils import logger
from src.utils.database import get_db_connection

async def execute_query_executor(dbname: str, query: str, download_excel: bool = False, conversation_name: str = "default_session") -> AsyncGenerator[str, None]:
    """
    Execute SQL query on actual database and optionally store output in session SQLite.
    Returns top 10 rows and success status.
    """
    logger.info(f"Executing query on {dbname}: {query}")

    result = {"database": dbname, "query": query, "rows": []}
    
    conn = None
    try:
        # Use existing connection logic from src.utils.database
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)

            if cursor.description:
                colnames = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
            else:
                colnames = []
                rows = []

        def serialize_value(val):
            if isinstance(val, Decimal):
                return str(val)
            elif isinstance(val, datetime):
                return val.strftime("%Y-%m-%d %H:%M:%S")
            return val

        all_rows = [
            {col: serialize_value(val) for col, val in zip(colnames, row)}
            for row in rows
        ]

        result["rows"] = all_rows[:10]
        result["success"] = True

        if download_excel:
            if all_rows:
                df = pd.DataFrame(all_rows)
                buffer = BytesIO()
                df.to_excel(buffer, index=False, engine="openpyxl")
                buffer.seek(0)

                excel_base64 = base64.b64encode(buffer.read()).decode("utf-8")
                filename = f"{dbname}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

                yield json.dumps({
                    "type": "file",
                    "filename": filename,
                    "filetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "content_base64": excel_base64,
                })
                yield "PostgreSQL query results exported to Excel."
                return
            else:
                yield "No rows returned to export to Excel."
                return

        # Simple SQLite session storage logic
        try:
            session_dir = Path("database_session")
            session_dir.mkdir(parents=True, exist_ok=True)
            db_path = session_dir / f"{conversation_name}.sqlite"

            db_config = {"db_type": "sqlite", "db_path": str(db_path)}
            with get_db_connection(db_config) as s_conn:
                s_cursor = s_conn.cursor()
                
                # Count existing query tables
                s_cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name LIKE 'query_%'")
                query_count = s_cursor.fetchone()[0]
                table_name = f"query_{query_count + 1}"

                if all_rows:
                    columns = all_rows[0].keys()
                    col_defs = ", ".join([f'"{col}" TEXT' for col in columns])
                    s_cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({col_defs})")

                    for row in all_rows:
                        placeholders = ", ".join(["?"] * len(row))
                        quoted_cols = ", ".join([f'"{col}"' for col in row.keys()])
                        s_cursor.execute(
                            f"INSERT INTO {table_name} ({quoted_cols}) VALUES ({placeholders})",
                            tuple(row.values()),
                        )
                else:
                    s_cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (message TEXT)")
                    s_cursor.execute(
                        f"INSERT INTO {table_name} (message) VALUES (?)",
                        ("No rows returned",),
                    )
                s_conn.commit()
        except Exception as se:
            logger.error(f"Error storing result in SQLite session: {se}")

    except Exception as e:
        result["success"] = False
        result["error"] = str(e)
        all_rows = []

    yield json.dumps({ "type": "frontend_data", "rows": all_rows[:10] })
    yield json.dumps(result, ensure_ascii=False)

execute_query_tool_session = Tool(
    name="execute_query",
    description="Execute SQL query on actual database and store output in session SQLite. Agent gets top 10 rows.",
    function=execute_query_executor,
    parameters=[
        ToolParam(
            name="dbname",
            type="string",
            description="database name (purchase, hr, engineering, etc).",
            required=True,
        ),
        ToolParam(
            name="query",
            type="string",
            description="SQL query to execute.",
            required=True,
        ),
        ToolParam(
            name="download_excel",
            type="boolean",
            description="Download full result as Excel.",
            required=False,
        ),
        ToolParam(
            name="conversation_name",
            type="string",
            description="Session identifier to persist results for subsequent merging.",
            required=False,
            default="default_session"
        ),
    ]
)

