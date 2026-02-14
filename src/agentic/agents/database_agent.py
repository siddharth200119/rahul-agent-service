import os
from typing import List, Optional
from RAW.agent import Agent
from RAW.modals import Message
from src.agentic.llms.primary import get_primary_llm
from src.utils import logger, get_db_cursor
from src.agentic.tools.database import __all__ as db_tools_list
from src.agentic.tools import database as db_tools_module

def load_db_schema(file_path: str) -> str:
    """
    Load the database schema file content.
    Returns string content or empty string if file not found.
    """
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return f"Schema file {file_path} not found."

def get_database_agent(user_id: int = None, history: List[Message] = [], module: str = None) -> Agent:
    db_info_dir = os.path.join("src", "db_info")
    db_schemas = []

    # Ensure the directory exists
    if not os.path.exists(db_info_dir):
        os.makedirs(db_info_dir, exist_ok=True)

    # Load only the schema for the selected module
    if module:
        schema_file = f"{module}.txt"
        file_path = os.path.join(db_info_dir, schema_file)
        schema_content = load_db_schema(file_path)
        db_schemas.append(f"--- {schema_file} ---\n{schema_content}")
    else:
        # fallback - if module not provided, load all
        try:
            for schema_file in os.listdir(db_info_dir):
                if schema_file.endswith(".txt"):
                    file_path = os.path.join(db_info_dir, schema_file)
                    schema_content = load_db_schema(file_path)
                    db_schemas.append(f"--- {schema_file} ---\n{schema_content}")
        except Exception as e:
            logger.error(f"Error reading db_info directory: {e}")

    combined_db_schema_info = "\n\n".join(db_schemas)


    base_prompt = f"""
You are a highly capable Database Assistant Agent. You have DIRECT access to databases through your provided tools.

### 🚨 CRITICAL SCHEMA VERIFICATION RULE:
You MUST ALWAYS call the `get_schema` tool FIRST for any table you intend to query. 
- **NEVER GUESS table names.** (e.g., Do NOT assume a table is named `inventory`; check `get_schema` to see if it is `inventory_units`).
- **NEVER GUESS column names.** Always verify via `get_schema` before writing SQL.
- If you encounter a "relation does not exist" error, it means you used the wrong table name. Immediately call `get_schema` to find the correct table.

### STRICT ANTI-HALLUCINATION RULES (MANDATORY):
1. **NEVER make up data.** If a query returns 0 rows, your summary must state that no data was found.
2. **NEVER assume a correction worked.** If a tool returns an error, you MUST explain the error or attempt a fix using a DIFFERENT tool. Do NOT pretend you found the right result if you didn't.
3. **ONLY report what is in the tool output.**
4. **NO GHOST TOOLS.** Do not talk about "checking the schema" unless you actually executed the tool.

### OPERATIONAL RULES:
1. **Always use your tools.** Choose the appropriate tool from your toolbox immediately.
2. **Workflow**: 
   - **Step 1**: Call `get_schema` for the relevant tables.
   - **Step 2**: Review the schema and write a precise SQL query.
   - **Step 3**: Execute the query using `execute_query`.
3. **Target Context**: You are primarily working with the 'erp' database.

### DATABASE SCHEMA & SPECIFIC LOGIC (READ CAREFULLY):
{combined_db_schema_info}

### RESPONSE FORMAT (MANDATORY):
- All final responses MUST be in valid Markdown.
- Include sections: 1. **Result Summary**, 2. **Notes / Assumptions**.
- **Verification**: In your "Notes" section, always state which tool/query was used to verify the data.

Proceed with the user's request. Remember: If the database is empty or the query fails, say so. DO NOT MAKE UP RESULTS.
"""

    llm = get_primary_llm()
    
    # Dynamically load all tools exported in src.agentic.tools.database
    tools = [getattr(db_tools_module, tool_name) for tool_name in db_tools_list]

    bot = Agent(
        name="Database agent",
        base_prompt=base_prompt,
        llm=llm,
        logger=logger,
        tools=tools,
        history=history
    )


    return bot
