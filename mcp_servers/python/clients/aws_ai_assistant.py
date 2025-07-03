#!/usr/bin/env python3
"""
AI-Powered AWS Assistant
Pure conversational interface - AI determines all AWS operations automatically
"""

import requests
import json
import sys
import os
from typing import Dict, Any, List
import time

class AWSAIAssistant:
    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.chat_history = []
        self.context = {
            "user_name": "User",
            "aws_region": "eu-north-1",
            "last_instances": [],
            "conversation_context": []
        }
    
    def call_ai_assistant(self, user_message: str) -> Dict[str, Any]:
        """Call the AI assistant to understand user intent and execute AWS operations"""
        
        # Build conversation context
        context_messages = []
        for msg in self.chat_history[-3:]:  # Last 3 exchanges for context
            context_messages.append(f"User: {msg['user']}")
            context_messages.append(f"Assistant: {msg['assistant_summary']}")
        
        context_str = "\n".join(context_messages) if context_messages else "This is the start of our conversation."
        
        # Create intelligent prompt for AI
        ai_prompt = f"""You are an AWS infrastructure assistant with access to AWS CLI tools through the aws_cli_pipeline function. 

Previous conversation context:
{context_str}

Current user message: "{user_message}"

IMPORTANT INSTRUCTIONS:
1. You MUST execute AWS CLI commands to fulfill user requests - do not just provide command suggestions
2. When the user asks about AWS resources, immediately call the aws_cli_pipeline function with appropriate AWS commands
3. Always use <function_call>TRUE</function_call> and specify the correct tool when the user needs AWS information or operations
4. Be conversational in your responses but ALWAYS execute the actual AWS commands

For the current user request, determine the appropriate AWS CLI command and EXECUTE it using the aws_cli_pipeline function. Do not just suggest commands - actually run them.

If the user is asking for AWS information or operations, you MUST respond with:
<function_call>TRUE</function_call>
<selected_tools>aws_cli_pipeline</selected_tools>

Then execute the appropriate AWS CLI command."""

        payload = {
            "selected_server_credentials": {
                "AWS-EC2": {
                    "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID", "your_access_key_id_here"),
                    "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY", "your_secret_access_key_here"),
                    "aws_region": os.getenv("AWS_REGION", "region_here"),
                }
            },
            "client_details": {
                "api_key": os.getenv("GEMINI_API_KEY", "your_api_key_here"),
                "temperature": 0.3,  # Slightly more creative for conversational responses
                "max_token": 25000,
                "input": user_message,
                "input_type": "text",
                "prompt": ai_prompt,
                "chat_model": "gemini-2.0-flash",
                "chat_history": self.build_chat_history()
            },
            "selected_client": "MCP_CLIENT_GEMINI",
            "selected_servers": ["AWS-EC2"]
        }
        
        try:
            print("🤖 AI Assistant is thinking...")
            # Use the correct endpoint from your MCP logs
            response = self.session.post(f"{self.base_url}/api/v1/mcp/process_message", json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to connect to AI assistant: {str(e)}"}
    
    def build_chat_history(self) -> List[Dict[str, str]]:
        """Build chat history for AI context"""
        history = []
        for msg in self.chat_history[-5:]:  # Last 5 exchanges
            history.append({"role": "user", "content": msg["user"]})
            history.append({"role": "assistant", "content": msg["assistant_summary"]})
        return history
    
    def extract_ai_response(self, response_data: Dict[str, Any]) -> str:
        """Extract and format the AI assistant's response"""
        if "error" in response_data:
            return f"❌ I'm having trouble connecting to AWS right now: {response_data['error']}"
        
        try:
            # Debug: Print response structure to understand format
            print(f"🔍 Debug - Response keys: {list(response_data.keys()) if response_data else 'None'}")
            
            if not response_data:
                return "❌ I received an empty response. Let me try that again."
            
            # Check for Error first
            if response_data.get("Error"):
                return f"❌ I encountered an error: {response_data['Error']}"
            
            # Check Status
            if not response_data.get("Status"):
                return "❌ The request was not successful. Let me try again."
            
            # Now safely access Data
            data = response_data.get("Data")
            if not data:
                return "❌ I received a successful response but no data was returned."
            
            print(f"🔍 Debug - Data keys: {list(data.keys()) if isinstance(data, dict) else 'Data is not a dict'}")
            
            # PRIORITY: Look for executed_tool_calls FIRST (actual AWS execution results)
            tool_calls = data.get("executed_tool_calls")
            if tool_calls and len(tool_calls) > 0:
                print(f"🔍 Debug - Found {len(tool_calls)} tool calls")
                
                for i, tool_call in enumerate(tool_calls):
                    print(f"🔍 Debug - Tool call {i}: {tool_call.get('name', 'unknown')}")
                    print(f"🔍 Debug - Tool call arguments: {tool_call.get('arguments', {})}")
                    
                    result = tool_call.get("result", {})
                    if result:
                        content = result.get("content", [])
                        if content and len(content) > 0:
                            text_content = content[0].get("text", "")
                            print(f"🔍 Debug - Tool result content: {text_content[:200]}...")
                            
                            if text_content:
                                try:
                                    # Parse the AWS execution result
                                    parsed = json.loads(text_content)
                                    if parsed.get("status") == "success":
                                        output = parsed.get("output", "")
                                        if output:
                                            # Try to parse AWS JSON output
                                            try:
                                                aws_data = json.loads(output)
                                                return self.format_aws_data_conversationally(aws_data, tool_call.get("name", ""))
                                            except json.JSONDecodeError:
                                                # If not JSON, return the raw output with context
                                                command = tool_call.get("arguments", {}).get("command", "AWS command")
                                                return f"✅ I executed: {command}\n\nResult:\n{output}"
                                        else:
                                            command = tool_call.get("arguments", {}).get("command", "AWS command")
                                            return f"✅ I successfully executed: {command}"
                                    else:
                                        error_msg = parsed.get("output", "Unknown error")
                                        command = tool_call.get("arguments", {}).get("command", "AWS command")
                                        return f"❌ Error executing: {command}\n\nError: {error_msg}"
                                except json.JSONDecodeError:
                                    # Raw text response
                                    command = tool_call.get("arguments", {}).get("command", "AWS command")
                                    return f"✅ I executed: {command}\n\nResult:\n{text_content}"
                    else:
                        print(f"🔍 Debug - No result found for tool call {i}")
            else:
                print("🔍 Debug - No tool calls found or empty tool calls list")
            
            # FALLBACK: Only if no tool calls, look for AI text response
            final_response = data.get("final_llm_response")
            if final_response:
                candidates = final_response.get("candidates", [])
                
                if candidates and len(candidates) > 0:
                    content = candidates[0].get("content", {})
                    if content:
                        parts = content.get("parts", [])
                        
                        for part in parts:
                            if isinstance(part, dict) and "text" in part:
                                text = part["text"]
                                # If the AI is giving commands instead of results, tell user
                                if "aws " in text.lower() and "```" in text:
                                    return "I see you want me to execute AWS commands, but I'm having trouble getting the execution results. Let me try a different approach."
                                return text
            
            return "I'm ready to help with your AWS infrastructure. What would you like me to do?"
            
        except Exception as e:
            print(f"🔍 Debug - Exception details: {str(e)}")
            print(f"🔍 Debug - Exception type: {type(e)}")
            return f"I encountered an issue while processing your request: {str(e)}"
    
    def format_aws_data_conversationally(self, aws_data: Dict[str, Any], query_type: str) -> str:
        """Format AWS data in a conversational way"""
        try:
            if "Instances" in aws_data and "OwnerId" in aws_data:
                # EC2 run-instances response (single instance creation)
                instances = aws_data.get("Instances", [])
                if instances:
                    instance = instances[0]
                    instance_id = instance.get("InstanceId")
                    instance_type = instance.get("InstanceType")
                    state = instance.get("State", {}).get("Name", "unknown")
                    az = instance.get("Placement", {}).get("AvailabilityZone")
                    
                    return f"🎉 Great! I successfully created a new EC2 instance for you!\n\n" \
                           f"✅ **Instance Details:**\n" \
                           f"   • Instance ID: {instance_id}\n" \
                           f"   • Type: {instance_type}\n" \
                           f"   • State: {state}\n" \
                           f"   • Location: {az}\n\n" \
                           f"Your instance is now {state}. It may take a few minutes to fully initialize."
            
            elif "Reservations" in aws_data:
                # EC2 describe-instances response
                reservations = aws_data["Reservations"]
                if not reservations:
                    return "I checked your EC2 instances and didn't find any in this region. Would you like me to help you create one?"
                
                instances = []
                for reservation in reservations:
                    for instance in reservation.get("Instances", []):
                        name = "Unnamed"
                        for tag in instance.get("Tags", []):
                            if tag.get("Key") == "Name":
                                name = tag.get("Value", "Unnamed")
                                break
                        
                        instances.append({
                            "id": instance.get("InstanceId"),
                            "name": name,
                            "state": instance.get("State", {}).get("Name"),
                            "type": instance.get("InstanceType"),
                            "az": instance.get("Placement", {}).get("AvailabilityZone"),
                            "public_ip": instance.get("PublicIpAddress"),
                            "private_ip": instance.get("PrivateIpAddress")
                        })
                
                if not instances:
                    return "I found your reservations but no instances are currently visible. This might be a permissions issue or the instances might be in a different region."
                
                response = f"📋 Here are your EC2 instances ({len(instances)} total):\n\n"
                
                running_count = 0
                pending_count = 0
                stopped_count = 0
                terminated_count = 0
                
                for instance in instances:
                    if instance["state"] == "running":
                        status_emoji = "🟢"
                        running_count += 1
                    elif instance["state"] == "pending":
                        status_emoji = "🟡"
                        pending_count += 1
                    elif instance["state"] == "stopped":
                        status_emoji = "🟠"
                        stopped_count += 1
                    elif instance["state"] == "terminated":
                        status_emoji = "🔴"
                        terminated_count += 1
                    else:
                        status_emoji = "⚪"
                    
                    response += f"{status_emoji} **{instance['name']}** ({instance['id']})\n"
                    response += f"   State: {instance['state']}, Type: {instance['type']}\n"
                    response += f"   Location: {instance['az']}\n"
                    
                    if instance['public_ip']:
                        response += f"   Public IP: {instance['public_ip']}\n"
                    if instance['private_ip']:
                        response += f"   Private IP: {instance['private_ip']}\n"
                    response += "\n"
                
                # Summary
                summary_parts = []
                if running_count > 0:
                    summary_parts.append(f"{running_count} running")
                if pending_count > 0:
                    summary_parts.append(f"{pending_count} starting up")
                if stopped_count > 0:
                    summary_parts.append(f"{stopped_count} stopped")
                if terminated_count > 0:
                    summary_parts.append(f"{terminated_count} terminated")
                
                if summary_parts:
                    response += f"📊 **Summary:** {', '.join(summary_parts)}\n\n"
                
                if running_count == 0 and pending_count == 0:
                    response += "💡 No instances are currently running, so you're not being charged for compute time."
                elif pending_count > 0:
                    response += f"⏳ {pending_count} instance{'s are' if pending_count > 1 else ' is'} starting up and will be ready soon."
                
                return response
            
            elif "Buckets" in aws_data:
                # S3 buckets
                buckets = aws_data["Buckets"]
                if not buckets:
                    return "I checked your S3 storage and you don't have any buckets yet. Would you like me to help you create one?"
                
                response = f"🪣 Here are your S3 buckets ({len(buckets)} total):\n\n"
                for bucket in buckets:
                    response += f"• **{bucket['Name']}** (created {bucket['CreationDate']})\n"
                
                return response
            
            elif "SecurityGroups" in aws_data:
                # Security groups
                groups = aws_data["SecurityGroups"]
                response = f"🔒 Here are your security groups ({len(groups)} total):\n\n"
                
                for group in groups:
                    response += f"• **{group['GroupName']}** ({group['GroupId']})\n"
                    response += f"  Description: {group.get('Description', 'No description')}\n"
                    response += f"  VPC: {group.get('VpcId', 'Classic')}\n\n"
                
                return response
            
            elif "Vpcs" in aws_data:
                # VPCs
                vpcs = aws_data["Vpcs"]
                response = f"🌐 Here are your VPCs ({len(vpcs)} total):\n\n"
                
                for vpc in vpcs:
                    is_default = "🏠 (Default)" if vpc.get("IsDefault") else ""
                    response += f"• **{vpc['VpcId']}** {is_default}\n"
                    response += f"  CIDR: {vpc.get('CidrBlock', 'Unknown')}\n"
                    response += f"  State: {vpc.get('State', 'Unknown')}\n\n"
                
                return response
            
            else:
                # Generic AWS data - try to make it readable
                if isinstance(aws_data, dict) and len(aws_data) == 1:
                    # Single key response, probably a simple result
                    key, value = next(iter(aws_data.items()))
                    if isinstance(value, list) and len(value) == 0:
                        return f"✅ I checked your {key.lower()} and found none in this region."
                    elif isinstance(value, str):
                        return f"✅ Result: {value}"
                
                return f"✅ Here's the information I retrieved:\n```json\n{json.dumps(aws_data, indent=2)}\n```"
                
        except Exception as e:
            return f"I retrieved the data but had trouble formatting it nicely. Here's the raw information:\n```json\n{json.dumps(aws_data, indent=2)}\n```"
    
    def run_conversation(self):
        """Run the conversational AI assistant"""
        print("🤖 AWS AI Assistant")
        print("=" * 50)
        print("Hi! I'm your intelligent AWS assistant. I can help you manage")
        print("and understand your AWS infrastructure using natural language.")
        print("")
        print("💬 Just talk to me naturally! For example:")
        print("  • 'What instances do I have running?'")
        print("  • 'Show me my storage situation'")
        print("  • 'How is my AWS infrastructure looking?'")
        print("  • 'What security groups are configured?'")
        print("  • 'Give me an overview of my AWS setup'")
        print("=" * 50)
        print("Type 'bye', 'quit', or 'exit' to end our conversation\n")
        
        # Welcome message
        print("🤖 Assistant: Hello! I'm ready to help you with your AWS infrastructure.")
        print("             What would you like to know about your AWS resources?")
        print()
        
        while True:
            try:
                user_input = input("💬 You: ").strip()
                
                if user_input.lower() in ['bye', 'quit', 'exit', 'goodbye']:
                    print("🤖 Assistant: Goodbye! Feel free to come back anytime you need help with AWS!")
                    break
                
                if not user_input:
                    continue
                
                # Show thinking indicator
                print("🤖 Assistant: Let me check that for you...")
                
                # Get AI response
                response = self.call_ai_assistant(user_input)
                ai_response = self.extract_ai_response(response)
                
                # Display AI response
                print(f"🤖 Assistant: {ai_response}")
                print()
                
                # Update chat history
                self.chat_history.append({
                    "user": user_input,
                    "assistant_summary": ai_response[:200] + "..." if len(ai_response) > 200 else ai_response,
                    "full_response": response
                })
                
                # Keep history manageable
                if len(self.chat_history) > 10:
                    self.chat_history = self.chat_history[-8:]
                
            except KeyboardInterrupt:
                print("\n🤖 Assistant: Goodbye! Have a great day!")
                break
            except Exception as e:
                print(f"🤖 Assistant: I encountered an error: {str(e)}")
                print("             Let's try that again.")

def main():
    """Main function"""
    print("🔍 Checking AI Assistant connection...")
    
    # Check if MCP client is running
    try:
        response = requests.get("http://localhost:5001", timeout=5)
        print("✅ MCP client is running at localhost:5001")
    except requests.exceptions.RequestException:
        print("❌ MCP client not found at localhost:5001")
        print("💡 Please start your MCP client first:")
        print("   cd mcp_servers/python/clients")
        print("   source venv/bin/activate") 
        print("   python run.py")
        print()
        print("Then run this assistant again!")
        sys.exit(1)
    
    # Check environment variables
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠️  Warning: GEMINI_API_KEY not set. Using default configuration.")
        print("   For best results, set your Gemini API key:")
        print("   export GEMINI_API_KEY='your_api_key_here'")
        print()
    
    print("🚀 Starting AI Assistant...")
    print()
    
    # Start AI assistant
    assistant = AWSAIAssistant()
    assistant.run_conversation()

if __name__ == "__main__":
    main()
