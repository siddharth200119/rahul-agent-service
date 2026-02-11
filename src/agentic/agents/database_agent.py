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

### OPERATIONAL RULES:
1. **Always use your tools.** If you need to know about tables, columns, or run a query, choose the appropriate tool from your toolbox immediately.
2. **Never refuse a request** by saying you don't have access. You HAVE access via your tools.
3. **Workflow**: 
   - First, explore the schema to verify table names and columns.
   - Then, execute the SQL query to get the data.
4. **Target Context**: You are primarily working with the 'erp' database.

### DATABASE SCHEMA & SPECIFIC LOGIC:
{combined_db_schema_info}

### RESPONSE FORMAT (MANDATORY):
- All final responses MUST be in valid Markdown.
- Use structured headers (`#`, `##`).
- Use Markdown tables for data.
- Include sections: 1. **Result Summary**, 2. **Notes / Assumptions**.
- Internal IDs should be hidden from the user summary.

Proceed with the user's request using your tools.
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
