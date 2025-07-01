from mcp.server.fastmcp import FastMCP
from agora.client import Agora
import os
from typing import Dict, List, Optional


# Create FastMCP instance
mcp = FastMCP("Fewsats MCP Server")


def get_agora():
    """Get or create an Agora instance. 
    We want to create the class instance inside the tool, 
    so the init errors will bubble up to the tool and hence the MCP client instead of silently failing
    during the server creation.
    """

    return Agora()


def handle_response(response):
    """
    Handle responses from Agora methods.
    """
    if hasattr(response, 'status_code'):
        # This is a raw response object
        try: return response.status_code, response.json()
        except: return response.status_code, response.text
    # This is already processed data (like a dictionary)
    return response


@mcp.tool()
async def agora_search(q: str, price_min: int = 0, price_max: int = 100000,
                count: int = 20, page: int = 1,
                sort: str = "relevance", order: str = "desc") -> Dict:
    """
    Search for products matching the query in Agora.
    
    Args:
        q: The search query.
        count: The number of products to return per page.
        page: The page number.
        price_min: The minimum price. Optional
        price_max: The maximum price. Optional
        sort: The sort field: price:relevance.
        order: The sort order: asc or desc.
        
    Returns:
        The search results.
    """
    response = get_agora().search_products(
        query=q,
        count=count,
        page=page,
        price_min=price_min,
        price_max=price_max,
        sort=sort,
        order=order
    )
    return handle_response(response)


@mcp.tool()
async def agora_get_product_detail(slug: str) -> Dict:
    """
    Get details for a specific product in Agora.
    
    Args:
        slug: The product slug, it usually looks something like 'royal-blue-waxed-shoe-laces-6f2049ef-0d08-4a79-8937-025bb596092f-1718242165922'
        
    Returns:
        The product details.
    """
    response = get_agora().get_product_detail(slug=slug)
    return handle_response(response)

@mcp.tool()
async def agora_get_payment_offers(slug: str, product_id: str , variant_id: str, shipping_address: Dict,
                 user: Dict, quantity: int = 1) -> Dict:
    """
    Get the payment offers for a product in Agora. Some products do not have variants, in such cases use the product_id as variant_id too.
    Before calling this tool, check if the user has already provided the shipping address and user information. 
    Otherwise, ask the user for the shipping address and user information.

    If the user does not provide an `addressName`, use the `firstname` and `lastname` to populate it.
    Args:
        slug: The product slug.
        product_id: The product ID as str delimited by escaped double quotes
        variant_id: The product variant ID as str delimited by escaped double quotes
        quantity: The quantity to purchase.
        shipping_address: The shipping address.
        user: The user information.
        
    Example:
        product_id = "\\"1234567890\\""
        variant_id = "\\"1234567890\\""
        shipping_address = {
            "addressName": "John Doe",
            "addressFirst": "123 Main St",
            "city": "New York",
            "state": "NY",
            "country": "US",
            "zipCode": "10001"
        }
        
        user = {
            "firstname": "John",
            "lastname": "Doe",
            "email": "john@example.com",
        }
        
    Returns:
        L402 offer that can be paid by L402-compatible clients.
    """
    response = get_agora().buy_now(
        slug=slug,
        product_id=product_id,
        variant_id=variant_id,
        quantity=quantity,
        shipping_address=shipping_address,
        user=user
    )
    return handle_response(response)


@mcp.tool()
async def agora_get_order(order_id: str) -> Dict:
    """
    Get details for a specific order in Agora.
    
    Args:
        order_id: The order ID.
        
    Returns:
        The order details.
    """
    response = get_agora().get_order(order_id=order_id)
    return handle_response(response)


@mcp.tool()
async def agora_get_user_orders() -> List[Dict]:
    """
    Get all orders for the current user.
    
    Returns:
        A list of orders.
    """
    response = get_agora().get_user_orders()
    return handle_response(response)


@mcp.tool()
async def agora_get_user_info() -> Dict:
    """
    Get the current user's profile and shipping addresses in Agora.
    
    Returns:
        Dict containing user profile info (firstname, lastname, email) and list of shipping addresses
    """
    response = get_agora().get_user_info()
    return handle_response(response)


def main():
    mcp.run()
