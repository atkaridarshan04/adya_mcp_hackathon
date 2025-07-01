import requests
import json
import sys

# Set UTF-8 encoding for output
sys.stdout.reconfigure(encoding='utf-8')

# API endpoint
url = "http://localhost:5001/api/v1/mcp/process_message"

# Correct request payload format
payload = {
    "selected_client": "MCP_CLIENT_OPENAI",
    "selected_servers": ["Agora"],
    "selected_server_credentials": {
        "message": "Search for t-shirts",
        "user_query": "Show me some t-shirts available for purchase"
    },
    "client_details": {
        "is_stream": False
    }
}

try:
    print("Searching for t-shirts using Agora server...")
    response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
    
    if response.status_code == 200:
        result = response.json()
        print("\nT-SHIRT SEARCH RESULTS:")
        print("=" * 50)
        
        if result.get("Status"):
            print("✅ Search successful!")
            if result.get("Data"):
                print(json.dumps(result["Data"], indent=2))
            else:
                print("No data returned")
        else:
            print("❌ Search failed:")
            print(f"Error: {result.get('Error', 'Unknown error')}")
            print(json.dumps(result, indent=2))
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ Error: {e}")