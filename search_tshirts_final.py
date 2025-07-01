import requests
import json
import sys

# Set UTF-8 encoding for output
sys.stdout.reconfigure(encoding='utf-8')

# API endpoint
url = "http://localhost:5001/api/v1/mcp/process_message"

# Correct request payload format based on Postman collection
payload = {
    "selected_server_credentials": {
        "Agora": {}  # Agora might not need credentials or they're handled internally
    },
    "client_details": {
        "api_key": "your-openai-api-key-here",  # You'll need to add your OpenAI API key
        "temperature": 0.1,
        "input": "Search for t-shirts using the agora_search tool. Show me available t-shirts for purchase.",
        "input_type": "text",
        "prompt": "you are a helpful assistant that helps users find products",
        "chat_model": "gpt-4o",
        "chat_history": [
            {
                "role": "user",
                "content": "Hi, I want to search for t-shirts"
            }
        ]
    },
    "selected_client": "MCP_CLIENT_OPENAI",
    "selected_servers": [
        "Agora"
    ]
}

try:
    print("🔍 Searching for t-shirts using Agora MCP server...")
    print("=" * 60)
    
    response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
    
    if response.status_code == 200:
        result = response.json()
        
        if result.get("Status"):
            print("✅ Search successful!")
            print("\n🛍️ T-SHIRT RESULTS:")
            print("-" * 40)
            
            if result.get("Data"):
                # Pretty print the results
                data = result["Data"]
                if isinstance(data, str):
                    print(data)
                else:
                    print(json.dumps(data, indent=2))
            else:
                print("No product data returned")
        else:
            print("❌ Search failed:")
            print(f"Error: {result.get('Error', 'Unknown error')}")
            print("\nFull response:")
            print(json.dumps(result, indent=2))
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        print("Response:", response.text)
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("Note: You may need to add your OpenAI API key to the script for it to work properly.")