import requests
import json

# API endpoint
url = "http://localhost:5001/api/v1/mcp/process_message"

# Request payload to search for t-shirts
payload = {
    "message": "Search for t-shirts",
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
    # Make the request
    response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
    
    if response.status_code == 200:
        result = response.json()
        print("🛍️ T-SHIRT SEARCH RESULTS:")
        print("=" * 50)
        print(json.dumps(result, indent=2))
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"Error making request: {e}")