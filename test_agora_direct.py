"""
Direct test of Agora MCP server functionality
This bypasses the LLM client and tests the Agora server directly
"""
import sys
import os
import asyncio

# Add the Agora server path to Python path
sys.path.append(r'c:\Users\anupb\Downloads\adya_mcp_hackathon\mcp_servers\python\servers\Agora\src')

try:
    from agora_mcp.server import agora_search
    print("✅ Successfully imported Agora server functions")
    
    async def test_tshirt_search():
        print("\n🔍 Testing direct t-shirt search...")
        print("=" * 50)
        
        try:
            # Test the agora_search function directly
            result = await agora_search(
                q="t-shirt",
                price_min=0,
                price_max=100,
                count=10,
                page=1,
                sort="relevance",
                order="desc"
            )
            
            print("✅ Search completed!")
            print("\n🛍️ T-SHIRT RESULTS:")
            print("-" * 30)
            
            if isinstance(result, tuple):
                status_code, data = result
                print(f"Status Code: {status_code}")
                print(f"Data: {data}")
            else:
                print("Result:", result)
                
        except Exception as e:
            print(f"❌ Error during search: {e}")
            print(f"Error type: {type(e)}")
    
    # Run the async test
    asyncio.run(test_tshirt_search())
    
except ImportError as e:
    print(f"❌ Could not import Agora server: {e}")
    print("This might be because the Agora client dependencies are not installed")
    print("\nTrying alternative approach...")
    
    # Alternative: Check if we can at least see the server structure
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "agora_server", 
            r"c:\Users\anupb\Downloads\adya_mcp_hackathon\mcp_servers\python\servers\Agora\src\agora_mcp\server.py"
        )
        module = importlib.util.module_from_spec(spec)
        print("✅ Agora server file found and accessible")
        print("📋 Available functions in the server:")
        
        # Read the file to show available functions
        with open(r"c:\Users\anupb\Downloads\adya_mcp_hackathon\mcp_servers\python\servers\Agora\src\agora_mcp\server.py", 'r') as f:
            content = f.read()
            
        # Extract function names
        import re
        functions = re.findall(r'async def (\w+)', content)
        for func in functions:
            print(f"  - {func}")
            
    except Exception as e2:
        print(f"❌ Alternative approach failed: {e2}")

print("\n" + "=" * 50)
print("💡 To see t-shirts, you need to:")
print("1. Have a valid OpenAI API key in the MCP client")
print("2. Or run the Agora server with proper dependencies")
print("3. The server connects to SearchAgora.com for product data")