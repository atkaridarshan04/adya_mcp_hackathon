import requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# API endpoint
url = "http://localhost:5001/api/v1/mcp/process_message"

# PUT YOUR API KEY HERE 👇
YOUR_API_KEY = ""  # Paste your OpenAI API key between the quotes

payload = {
    "selected_server_credentials": {
        "Agora": {}
    },
    "client_details": {
        "api_key": YOUR_API_KEY,  # 👈 API KEY GOES HERE
        "temperature": 0.1,
        "input": "Search for cool t-shirts under $50",
        "input_type": "text",
        "prompt": "you are a helpful shopping assistant",
        "chat_model": "gpt-4o",
        "chat_history": []
    },
    "selected_client": "MCP_CLIENT_OPENAI",
    "selected_servers": ["Agora"]
}

try:
    print("🔍 Searching for t-shirts...")
    response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
    
    if response.status_code == 200:
        result = response.json()
        if result.get("Status"):
            print("✅ Found t-shirts!")
            print(json.dumps(result["Data"], indent=2))
        else:
            print("❌ Error:", result.get("Error"))
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        
except Exception as e:
    print(f"❌ Error: {e}")