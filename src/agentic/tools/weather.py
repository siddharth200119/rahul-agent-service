from RAW.modals import Tool
from RAW.modals.tools import ToolParam

async def get_weather(location: str):
    """Get the weather for a location."""
    # Mock weather data
    return f"The weather in {location} is sunny with a temperature of 25°C."

weather_tool = Tool(
    name="get_weather",
    description="Get the weather for a specific location",
    parameters=[
        ToolParam(name="location", type="string", description="The city and state, e.g. San Francisco, CA", required=True)
    ],
    function=get_weather
)
