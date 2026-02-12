import httpx
from RAW.modals import Tool
from RAW.modals.tools import ToolParam
from src.utils import logger

async def create_inquiry(user_id: int, product_interest: str, additional_notes: str = ""):
    """Creates a formal inquiry in the database via API when a user shows interest."""
    api_url = "https://your-api-endpoint.com/v1/inquiries"
    payload = {
        "user_id": user_id,
        "product_interest": product_interest,
        "notes": additional_notes
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, json=payload, timeout=10.0)
            response.raise_for_status()
            return "Success: Inquiry has been recorded. A representative will contact you with pricing details."
    except Exception as e:
        logger.error(f"Failed to create inquiry: {e}")
        return "Error: Could not record inquiry at this time. Please try again later."

create_inquiry_tool = Tool(
    name="create_inquiry",
    description="Call this tool when a user expresses interest in a product or service to record their lead.",
    parameters=[
        ToolParam(name="user_id", type="integer", description="The ID of the user", required=True),
        ToolParam(name="product_interest", type="string", description="The product or service the user is interested in", required=True),
        ToolParam(name="additional_notes", type="string", description="Any specific preferences or context from the user", required=False)
    ],
    function=create_inquiry
)