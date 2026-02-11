from RAW.agent import Agent
from RAW.modals import Message
from src.utils import logger
from src.agentic.llms.primary import get_primary_llm
from src.agentic.tools.weather import weather_tool
from src.agentic.tools.database.get_schema import get_schema_tool

def get_test_agent(user_id: int, history: list[Message] = []) -> Agent:
    """
    Returns a configured Test Agent instance.
    """
    llm = get_primary_llm()
    name = "TestAgent"
    
    # We can customize the base prompt here or pass it in
    base_prompt = f"You are {name}, a helpful assistant. Use the provided tools if needed."
    
    return Agent(
        name=name,
        base_prompt=base_prompt,
        tools=[weather_tool, get_schema_tool],
        llm=llm,
        logger=logger,
        history=history
    )
