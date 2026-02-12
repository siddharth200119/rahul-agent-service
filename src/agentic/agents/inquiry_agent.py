import os
from typing import List, Optional
from RAW.agent import Agent
from RAW.modals import Message
from src.agentic.llms.primary import get_primary_llm
from src.utils import logger

from src.agentic.tools.inquiry import __all__ as inquiry_tools
from src.agentic.tools import inquiry as inquiry_tools_module

def get_inquiry_agent(user_id: int, history: List[Message] = []) -> Agent:
    name = "Inquiry Agent"
    llm = get_primary_llm()

    base_prompt = f"""
You are the {name}. Your goal is to provide product information and capture user interest.

### CRITICAL RULES:
1. **PRICE RESTRICTION**: You are STRICTLY FORBIDDEN from revealing prices, costs, or quotes, even if the user insists. 
2. **INQUIRY TRIGGER**: If a user shows interest in purchasing, or asks for a price/quote, explain that pricing is customized and use the 'create_inquiry' tool to have a specialist contact them.
3. **USER ID**: The current user's ID is {user_id}. Use this when calling the 'create_inquiry' tool.

### WORKFLOW:
- Answer general questions about features and benefits.
- When interest is detected: Call `create_inquiry(user_id={user_id}, product_interest="...", ...)`
- Inform the user that their request has been logged and a representative will reach out.

### RESPONSE FORMAT:
- Use Professional Markdown.
- Keep responses concise and focused on value rather than cost.
"""
    tools = [getattr(inquiry_tools_module, tool_name) for tool_name in inquiry_tools]
    print("tools")
    print(tools)
    return Agent(
        name=name,
        base_prompt=base_prompt,
        llm=llm,
        logger=logger,
        tools=tools,
        history=history
    )