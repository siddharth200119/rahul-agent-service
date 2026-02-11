import json
import pandas as pd
import base64
from io import BytesIO
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator

from RAW.modals import Tool
from RAW.modals.tools import ToolParam
from src.utils import logger
from src.utils.database import get_db_connection

async def final_merge_executor(query: str, download_excel: bool = False, conversation_name: str = "default_session") -> AsyncGenerator[str, None]:
    """
    Execute custom SQL on session SQLite to merge/join previous query outputs.
    """
    logger.info(f"Executing final merge query: {query}")
    result = {"query": query, "rows": []}

    try:
        # Using the same naming convention as in execute_query.py
        db_path = Path("database_session") / f"{conversation_name}.sqlite"
        if not db_path.exists():
            yield json.dumps({"success": False, "error": f"Session database not found: {db_path}"})
            return

        db_config = {"db_type": "sqlite", "db_path": str(db_path)}
        with get_db_connection(db_config) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            
            colnames = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            
            result["rows"] = [dict(zip(colnames, row)) for row in rows]
            result["success"] = True
            
            if download_excel:
                if result["rows"]:
                    df = pd.DataFrame(result["rows"])
                    buffer = BytesIO()
                    df.to_excel(buffer, index=False, engine='openpyxl')
                    buffer.seek(0)
                    excel_base64 = base64.b64encode(buffer.read()).decode('utf-8')
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"merged_query_export_{timestamp}.xlsx"
                    
                    yield json.dumps({
                        "type": "file",
                        "filename": filename,
                        "filetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        "content_base64": excel_base64
                    })
                    yield f"Merged query results exported to Excel."
                    return
                else:
                    yield "No rows returned to export to Excel."
                    return

    except Exception as e:
        logger.error(f"Error in final merge: {e}")
        result["success"] = False
        result["error"] = str(e)

    yield json.dumps(result, ensure_ascii=False)

final_merge_tool_session = Tool(
    name="merge_results",
    description="Execute custom SQL on session SQLite to merge/join previous query outputs (without storing result).",
    function=final_merge_executor,
    parameters=[
        ToolParam(
            name="query",
            type="string",
            description="SQL query to execute on session-specific SQLite (can reference query_1, query_2, etc).",
            required=True
        ),
        ToolParam(
            name="download_excel",
            type="boolean",
            description="Whether to download the query results as an Excel file.",
            required=False
        ),
        ToolParam(
            name="conversation_name",
            type="string",
            description="Session identifier to access persisted results.",
            required=False,
            default="default_session"
        )
    ]
)

