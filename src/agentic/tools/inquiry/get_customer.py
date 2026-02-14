
import os
import httpx
from RAW.modals import Tool
from RAW.modals.tools import ToolParam
from src.utils import logger

API_BASE_URL = os.getenv("BACKEND_HOST", "http://192.168.1.62:3000")

async def get_customers(name_query: str):
    """Search for a customer/entity by name to retrieve their ID."""
    url = f"{API_BASE_URL}/v1/admin-service/entities/list"
    payload = {
        "skip": 0,
        "limit": 10,
        "filter": [{"field": "name", "operator": "contains", "value": name_query}]
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            data = response.json()
            # Expecting a list of entities in the response
            data = data.get("data", {}) or data # Adjust based on actual API response nesting
            entities = data.get("entities", [])
            if not entities:
                return f"No customers found matching '{name_query}'."
            
            result_str = "Found customers:\n"
            for ent in entities[:5]:
                result_str += f"id = {ent['id']} : name = {ent['name']}\n"
            return result_str
    except Exception as e:
        logger.error(f"Error fetching customers: {e}")
        return "Error fetching customer list."

get_customers_tool = Tool(
    name="get_customers",
    description="Search for a customer/company by name to get their customer_id.",
    parameters=[ToolParam(name="name_query", type="string", description="Part of the company name", required=True)],
    function=get_customers
)