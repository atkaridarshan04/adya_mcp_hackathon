import requests
import json
import sys

# Set UTF-8 encoding for output
sys.stdout.reconfigure(encoding='utf-8')

# API endpoint
url = "http://localhost:5001/api/v1/mcp/process_message"

# Request payload to search for t-shirts
payload = {
    "message": "Search for t-shirts using agora_search tool with query 't-shirt'",
    "client_details": {
        "client_name": "MCP_CLIENT_OPENAI",
        "is_stream": False
    },
    "server_details": {
        "server_name": "Agora",
        "tools": ["agora_search"]
    }
}

try:
    print("Searching for t-shirts...")
    response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
    
    if response.status_code == 200:
        result = response.json()
        print("\nT-SHIRT SEARCH RESULTS:")
        print("=" * 50)
        
        if result.get("Status") and result.get("Data"):
            print("Search successful!")
            print(json.dumps(result["Data"], indent=2))
        else:
            print("Search failed or no results:")
            print(json.dumps(result, indent=2))
    else:
        print(f"HTTP Error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"Error: {e}")