from RAW.modals import Tool
from RAW.modals.tools import ToolParam
from src.utils import logger, get_db_cursor

async def search_products(query: str):
    """
    Search for products in the database based on a keyword provided by the user.
    Returns a list of product names and their SKUs.
    """
    sql = """
        SELECT id, product_name, sku_code 
        FROM product_list 
        WHERE product_name ILIKE %s 
        OR attributes::text ILIKE %s
        LIMIT 10
    """
    search_term = f"%{query}%"
    
    try:
        # Using the existing get_db_cursor from your db file
        with get_db_cursor(profile="backend") as cur:
            cur.execute(sql, (search_term, search_term))
            results = cur.fetchall()
            
            if not results:
                return f"No products found matching '{query}'."
            
            # Formatting the output for the Agent to read
            product_list = "\n".join([f"id = {r['id']} : name =  {r['product_name']} (SKU: {r['sku_code']})" for r in results])
            return f"Found the following products for '{query}':\n{product_list}"
            
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        return "Error: Unable to fetch product list at this time."

search_products_tool = Tool(
    name="search_products",
    description="Search the product catalog for available items by name or category.",
    parameters=[
        ToolParam(
            name="query", 
            type="string", 
            description="The product name or category to search for (e.g., 'papers', 'pens')", 
            required=True
        )
    ],
    function=search_products
)