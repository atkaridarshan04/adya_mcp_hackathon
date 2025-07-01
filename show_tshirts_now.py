import requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
url = "http://localhost:5001/api/v1/mcp/process_message"

payload = {
    "selected_server_credentials": {
        "Agora": {}
    },
    "client_details": {
        "api_key": "AIzaSyBeUKcWm-wzWX26_m8wZtae9j3MYLi-Pu8",
        "temperature": 0.1,
        "input": "Search for t-shirts using agora_search",
        "input_type": "text",
        "prompt": "you are a helpful shopping assistant",
        "chat_model": "gemini-2.0-flash",
        "chat_history": []
    },
    "selected_client": "MCP_CLIENT_GEMINI",
    "selected_servers": ["Agora"]
}

try:
    print("🛍️ Searching for t-shirts...")
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("Status"):
            print("✅ T-SHIRTS FOUND!")
            print(json.dumps(result["Data"], indent=2))
        else:
            print("❌ Error:", result.get("Error"))
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ Error: {e}")