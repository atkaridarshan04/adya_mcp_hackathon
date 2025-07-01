"""
T-Shirt Demo using your Agora MCP Server
This shows what your server can do for t-shirt shopping
"""
import json

print("=" * 60)
print("         T-SHIRT SHOPPING WITH YOUR AGORA MCP SERVER")
print("=" * 60)

print("\nYour Agora MCP server is designed to search for products including t-shirts!")
print("Here's what it can do:\n")

# Show the available functions from your server
functions = [
    {
        "name": "agora_search",
        "description": "Search for products matching the query in Agora",
        "example": "Search for 't-shirt' with price range $10-$50"
    },
    {
        "name": "agora_get_product_detail", 
        "description": "Get details for a specific product",
        "example": "Get details for a specific t-shirt"
    },
    {
        "name": "agora_get_payment_offers",
        "description": "Get payment offers for a product",
        "example": "Get payment options for purchasing a t-shirt"
    }
]

print("AVAILABLE FUNCTIONS:")
print("-" * 30)
for func in functions:
    print(f"• {func['name']}")
    print(f"  {func['description']}")
    print(f"  Example: {func['example']}")
    print()

print("SAMPLE T-SHIRT SEARCH REQUEST:")
print("-" * 35)
sample_request = {
    "function": "agora_search",
    "parameters": {
        "q": "t-shirt",
        "price_min": 10,
        "price_max": 50,
        "count": 10,
        "page": 1,
        "sort": "relevance",
        "order": "desc"
    }
}
print(json.dumps(sample_request, indent=2))

print("\nHOW TO USE YOUR SERVER:")
print("-" * 25)
print("1. Make sure your MCP client is running (localhost:5001)")
print("2. Add a valid OpenAI API key to your request")
print("3. Send a request like this:")

demo_payload = {
    "selected_server_credentials": {"Agora": {}},
    "client_details": {
        "api_key": "your-openai-api-key",
        "temperature": 0.1,
        "input": "Search for cool t-shirts under $30",
        "input_type": "text",
        "prompt": "you are a helpful shopping assistant",
        "chat_model": "gpt-4o"
    },
    "selected_client": "MCP_CLIENT_OPENAI",
    "selected_servers": ["Agora"]
}

print(json.dumps(demo_payload, indent=2))

print("\n" + "=" * 60)
print("Your Agora server connects to SearchAgora.com to find real products!")
print("It can search, filter by price, and help you purchase t-shirts.")
print("=" * 60)