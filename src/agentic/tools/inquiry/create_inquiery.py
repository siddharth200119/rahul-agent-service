import os
import httpx
from RAW.modals import Tool
from RAW.modals.tools import ToolParam
from src.utils import logger

# Configuration - Ensure these are in your .env
API_BASE_URL = os.getenv("BACKEND_HOST", "http://192.168.1.62:3000")

async def create_inquiry(
    expected_delivery_date: str,
    customer_id: int,
    poc_id: int,
    customer_name: str,
    poc_name: str,
    phone_number: str,
    product_id: int,
    product_name: str,
    quantity: int,
    uom_id: int,
    unit_price: float,
    size: str = "",
    gsm: int = 0,
    specifications: str = ""
):
    """
    Submits a formal inquiry with full customer and product details to the ERP system.
    """
    url = f"{API_BASE_URL}/v1/inquiries-service"
    
    # Building the complex nested payload according to your requirement
    payload = {
        "source": "WHATSAPP",
        "source_reference": None,
        "linked_order_id": None,
        "expected_delivery_date": expected_delivery_date,
        "special_instructions": specifications,
        "transcript": None,
        "assigned_sales_person": None,
        "is_within_working_hours": True,
        "interaction_due_time": f"{expected_delivery_date}T10:40", # Defaulting time
        "sla_status": "",
        "customer": {
            "customer_id": customer_id,
            "poc_id": poc_id,
            "name": customer_name,
            "poc_name": poc_name,
            "phone_number": phone_number,
            "whatsapp_number": phone_number,
            "email": "", 
            "address": "",
            "preferred_contact_method": "WHATSAPP"
        },
        "products": [
            {
                "product_id": product_id,
                "product_name": product_name,
                "quantity": quantity,
                "uom_id": uom_id,
                "unit_price": unit_price,
                "size": size,
                "gsm": gsm,
                "specifications": specifications
            }
        ]
    }
    print(f"Payload : {payload}")
    try:    
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return "SUCCESS: The inquiry has been officially created in the system."
    except Exception as e:
        logger.error(f"Failed to create inquiry: {e}")
        return f"ERROR: Failed to create inquiry. {str(e)}"

create_inquiry_tool = Tool(
    name="create_inquiry",
    description="Finalizes and submits the inquiry after all customer and product details are gathered.",
    parameters=[
        ToolParam(name="expected_delivery_date", type="string", description="Date in YYYY-MM-DD format", required=True),
        ToolParam(name="customer_id", type="integer", description="The ID of the customer entity", required=True),
        ToolParam(name="poc_id", type="integer", description="The ID of the Point of Contact", required=True),
        ToolParam(name="customer_name", type="string", description="Full name of the customer/company", required=True),
        ToolParam(name="poc_name", type="string", description="Name of the Point of Contact", required=True),
        ToolParam(name="phone_number", type="string", description="Contact phone number", required=True),
        ToolParam(name="product_id", type="integer", description="The ID of the selected product", required=True),
        ToolParam(name="product_name", type="string", description="Full name of the product", required=True),
        ToolParam(name="quantity", type="integer", description="Quantity required", required=True),
        ToolParam(name="uom_id", type="integer", description="The ID for Unit of Measure", required=True),
        ToolParam(name="unit_price", type="number", description="Target unit price", required=True),
        ToolParam(name="size", type="string", description="Product dimensions/size", required=False),
        ToolParam(name="gsm", type="integer", description="Paper GSM if applicable", required=False),
        ToolParam(name="specifications", type="string", description="Additional specs or instructions", required=False)
    ],
    function=create_inquiry
)