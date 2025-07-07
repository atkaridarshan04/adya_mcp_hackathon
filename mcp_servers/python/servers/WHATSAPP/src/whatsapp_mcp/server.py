"""WhatsApp MCP Server implementation with robust error handling."""

import asyncio
import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from mcp.server import Server
from mcp.server.lowlevel import NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
)

from whatsapp_mcp.modules import auth, group, message

# Logging configuration - ensure all logs go to stderr for MCP protocol compliance
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)


def extract_credentials(arguments: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Extract credentials from __credentials__ parameter."""
    credentials_obj = arguments.get("__credentials__")
    if credentials_obj:
        return {
            "GREENAPI_ID_INSTANCE": credentials_obj.get("GREENAPI_ID_INSTANCE"),
            "GREENAPI_API_TOKEN": credentials_obj.get("GREENAPI_API_TOKEN")
        }
    return None


def safe_json_serialize(obj: Any) -> str:
    """Safely serialize objects to JSON, handling non-serializable types."""
    def json_serializer(obj):
        """Custom JSON serializer for non-serializable objects."""
        if hasattr(obj, 'data'):
            return obj.data
        elif hasattr(obj, 'json'):
            try:
                return obj.json()
            except:
                return str(obj)
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)
    
    try:
        return json.dumps(obj, default=json_serializer, indent=2)
    except Exception as e:
        logger.error(f"JSON serialization error: {e}")
        return json.dumps({"error": f"Serialization failed: {str(e)}", "data": str(obj)})


# Create the MCP server
server = Server("whatsapp-mcp-server")


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available WhatsApp tools."""
    return [
        Tool(
            name="open_session",
            description="Open a new WhatsApp session",
            inputSchema={
                "type": "object",
                "properties": {
                    "__credentials__": {
                        "type": "object",
                        "properties": {
                            "GREENAPI_ID_INSTANCE": {"type": "string"},
                            "GREENAPI_API_TOKEN": {"type": "string"}
                        },
                        "description": "WhatsApp API credentials"
                    }
                },
                "additionalProperties": True
            }
        ),
        Tool(
            name="close_session",
            description="Close the current WhatsApp session",
            inputSchema={
                "type": "object",
                "properties": {
                    "__credentials__": {
                        "type": "object",
                        "properties": {
                            "GREENAPI_ID_INSTANCE": {"type": "string"},
                            "GREENAPI_API_TOKEN": {"type": "string"}
                        },
                        "description": "WhatsApp API credentials (optional, not used for closing session)"
                    }
                },
                "additionalProperties": True
            }
        ),
        Tool(
            name="get_session_status",
            description="Get the current session status",
            inputSchema={
                "type": "object",
                "properties": {
                    "__credentials__": {
                        "type": "object",
                        "properties": {
                            "GREENAPI_ID_INSTANCE": {"type": "string"},
                            "GREENAPI_API_TOKEN": {"type": "string"}
                        },
                        "description": "WhatsApp API credentials (optional, not used for status check)"
                    }
                },
                "additionalProperties": True
            }
        ),
        Tool(
            name="send_message",
            description="Send a message to a WhatsApp contact",
            inputSchema={
                "type": "object",
                "properties": {
                    "phone_number": {
                        "type": "string",
                        "description": "Phone number with country code (e.g., '919876543210@c.us')"
                    },
                    "content": {
                        "type": "string",
                        "description": "Message content to send"
                    },
                    "reply_to": {
                        "type": "string",
                        "description": "ID of message to reply to (optional)"
                    },
                    "__credentials__": {
                        "type": "object",
                        "properties": {
                            "GREENAPI_ID_INSTANCE": {"type": "string"},
                            "GREENAPI_API_TOKEN": {"type": "string"}
                        },
                        "description": "WhatsApp API credentials (optional if session exists)"
                    }
                },
                "required": ["phone_number", "content"],
                "additionalProperties": True
            }
        ),
        Tool(
            name="get_chats",
            description="Get a list of chats with pagination",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of chats to return (default: 50)",
                        "default": 50
                    },
                    "offset": {
                        "type": "integer", 
                        "description": "Offset for pagination (default: 0)",
                        "default": 0
                    },
                    "__credentials__": {
                        "type": "object",
                        "properties": {
                            "GREENAPI_ID_INSTANCE": {"type": "string"},
                            "GREENAPI_API_TOKEN": {"type": "string"}
                        },
                        "description": "WhatsApp API credentials (optional if session exists)"
                    }
                },
                "additionalProperties": True
            }
        ),
        Tool(
            name="create_group",
            description="Create a new WhatsApp group",
            inputSchema={
                "type": "object",
                "properties": {
                    "group_name": {
                        "type": "string",
                        "description": "Name of the group to create"
                    },
                    "participants": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of participant phone numbers (e.g., ['919876543210@c.us'])"
                    },
                    "__credentials__": {
                        "type": "object",
                        "properties": {
                            "GREENAPI_ID_INSTANCE": {"type": "string"},
                            "GREENAPI_API_TOKEN": {"type": "string"}
                        },
                        "description": "WhatsApp API credentials (optional if session exists)"
                    }
                },
                "required": ["group_name", "participants"],
                "additionalProperties": True
            }
        ),
        Tool(
            name="get_group_participants",
            description="Get participants of a WhatsApp group",
            inputSchema={
                "type": "object",
                "properties": {
                    "group_id": {
                        "type": "string",
                        "description": "WhatsApp group ID"
                    },
                    "__credentials__": {
                        "type": "object",
                        "properties": {
                            "GREENAPI_ID_INSTANCE": {"type": "string"},
                            "GREENAPI_API_TOKEN": {"type": "string"}
                        },
                        "description": "WhatsApp API credentials (optional if session exists)"
                    }
                },
                "required": ["group_id"],
                "additionalProperties": True
            }
        ),
        Tool(
            name="get_account_info",
            description="Get WhatsApp account information",
            inputSchema={
                "type": "object",
                "properties": {
                    "__credentials__": {
                        "type": "object",
                        "properties": {
                            "GREENAPI_ID_INSTANCE": {"type": "string"},
                            "GREENAPI_API_TOKEN": {"type": "string"}
                        },
                        "description": "WhatsApp API credentials (optional if session exists)"
                    }
                },
                "additionalProperties": True
            }
        ),
        Tool(
            name="get_chat_history",
            description="Get message history for a specific chat",
            inputSchema={
                "type": "object",
                "properties": {
                    "chat_id": {
                        "type": "string",
                        "description": "Chat ID to get history for (e.g., '919876543210@c.us' or group ID)"
                    },
                    "count": {
                        "type": "integer",
                        "description": "Number of messages to retrieve (default: 100)",
                        "default": 100
                    },
                    "__credentials__": {
                        "type": "object",
                        "properties": {
                            "GREENAPI_ID_INSTANCE": {"type": "string"},
                            "GREENAPI_API_TOKEN": {"type": "string"}
                        },
                        "description": "WhatsApp API credentials (optional if session exists)"
                    }
                },
                "required": ["chat_id"],
                "additionalProperties": True
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls with comprehensive error handling."""
    try:
        logger.info(f"Executing tool: {name} with arguments: {arguments}")
        
        if name == "open_session":
            try:
                credentials = extract_credentials(arguments)
                success, message_text = await auth.auth_manager.open_session(credentials)
                result = safe_json_serialize({
                    "success": success,
                    "message": message_text,
                    "status": "session_opened" if success else "session_failed",
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error in open_session: {e}")
                result = safe_json_serialize({
                    "success": False,
                    "message": f"Failed to open session: {str(e)}",
                    "status": "error",
                    "timestamp": datetime.now().isoformat()
                })
            
        elif name == "close_session":
            try:
                success, message_text = auth.auth_manager.close_session()
                result = safe_json_serialize({
                    "success": success,
                    "message": message_text,
                    "status": "session_closed" if success else "close_failed",
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error in close_session: {e}")
                result = safe_json_serialize({
                    "success": False,
                    "message": f"Failed to close session: {str(e)}",
                    "status": "error",
                    "timestamp": datetime.now().isoformat()
                })
            
        elif name == "get_session_status":
            try:
                status = auth.auth_manager.get_session_status()
                result = safe_json_serialize({
                    "success": True,
                    "status": status,
                    "message": "Session status retrieved successfully",
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error in get_session_status: {e}")
                result = safe_json_serialize({
                    "success": False,
                    "status": {"authenticated": False, "state": "error", "message": f"Error: {str(e)}"},
                    "message": f"Failed to get session status: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                })
            
        elif name == "send_message":
            try:
                credentials = extract_credentials(arguments)
                phone_number = arguments.get("phone_number")
                content = arguments.get("content")
                reply_to = arguments.get("reply_to")
                
                # Validate required parameters
                if not phone_number:
                    result = safe_json_serialize({
                        "success": False,
                        "message": "Missing required parameter: phone_number",
                        "status": "validation_error",
                        "timestamp": datetime.now().isoformat()
                    })
                elif not content:
                    result = safe_json_serialize({
                        "success": False,
                        "message": "Missing required parameter: content",
                        "status": "validation_error",
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    # Auto-authenticate if credentials provided and no session exists
                    if not auth.auth_manager.is_authenticated() and credentials:
                        success, _ = await auth.auth_manager.open_session(credentials)
                        if not success:
                            result = safe_json_serialize({
                                "success": False,
                                "message": "Failed to authenticate with provided credentials",
                                "status": "authentication_failed",
                                "timestamp": datetime.now().isoformat()
                            })
                        else:
                            message_result = await message.send_message(
                                phone_number=phone_number, content=content, reply_to=reply_to
                            )
                            message_result["success"] = True
                            message_result["timestamp"] = datetime.now().isoformat()
                            result = safe_json_serialize(message_result)
                    elif not auth.auth_manager.is_authenticated():
                        result = safe_json_serialize({
                            "success": False,
                            "message": "No active session. Please open a session first or provide credentials.",
                            "status": "no_session",
                            "timestamp": datetime.now().isoformat()
                        })
                    else:
                        message_result = await message.send_message(
                            phone_number=phone_number, content=content, reply_to=reply_to
                        )
                        message_result["success"] = True
                        message_result["timestamp"] = datetime.now().isoformat()
                        result = safe_json_serialize(message_result)
            except Exception as e:
                logger.error(f"Error in send_message: {e}")
                result = safe_json_serialize({
                    "success": False,
                    "message": f"Failed to send message: {str(e)}",
                    "status": "error",
                    "timestamp": datetime.now().isoformat()
                })
                
        elif name == "get_chats":
            try:
                credentials = extract_credentials(arguments)
                limit = arguments.get("limit", 50)
                offset = arguments.get("offset", 0)
                
                # Validate parameters
                if not isinstance(limit, int) or limit <= 0:
                    limit = 50
                if not isinstance(offset, int) or offset < 0:
                    offset = 0
                
                # Auto-authenticate if credentials provided and no session exists
                if not auth.auth_manager.is_authenticated() and credentials:
                    success, _ = await auth.auth_manager.open_session(credentials)
                    if not success:
                        result = safe_json_serialize({
                            "success": False,
                            "message": "Failed to authenticate with provided credentials",
                            "chats": [],
                            "total": 0,
                            "status": "authentication_failed",
                            "timestamp": datetime.now().isoformat()
                        })
                    else:
                        chats = await message.get_chats(limit=limit, offset=offset)
                        result = safe_json_serialize({
                            "success": True,
                            "chats": chats,
                            "total": len(chats),
                            "limit": limit,
                            "offset": offset,
                            "status": "success",
                            "timestamp": datetime.now().isoformat()
                        })
                elif not auth.auth_manager.is_authenticated():
                    result = safe_json_serialize({
                        "success": False,
                        "message": "No active session. Please open a session first or provide credentials.",
                        "chats": [],
                        "total": 0,
                        "status": "no_session",
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    chats = await message.get_chats(limit=limit, offset=offset)
                    result = safe_json_serialize({
                        "success": True,
                        "chats": chats,
                        "total": len(chats),
                        "limit": limit,
                        "offset": offset,
                        "status": "success",
                        "timestamp": datetime.now().isoformat()
                    })
            except Exception as e:
                logger.error(f"Error in get_chats: {e}")
                result = safe_json_serialize({
                    "success": False,
                    "message": f"Failed to get chats: {str(e)}",
                    "chats": [],
                    "total": 0,
                    "status": "error",
                    "timestamp": datetime.now().isoformat()
                })
                
        elif name == "create_group":
            try:
                credentials = extract_credentials(arguments)
                group_name = arguments.get("group_name")
                participants = arguments.get("participants", [])
                
                # Validate required parameters
                if not group_name:
                    result = safe_json_serialize({
                        "success": False,
                        "message": "Missing required parameter: group_name",
                        "status": "validation_error",
                        "timestamp": datetime.now().isoformat()
                    })
                elif not participants or not isinstance(participants, list):
                    result = safe_json_serialize({
                        "success": False,
                        "message": "Missing or invalid required parameter: participants (must be a list)",
                        "status": "validation_error",
                        "timestamp": datetime.now().isoformat()
                    })
                elif len(participants) == 0:
                    result = safe_json_serialize({
                        "success": False,
                        "message": "Participants list cannot be empty",
                        "status": "validation_error",
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    # Auto-authenticate if credentials provided and no session exists
                    if not auth.auth_manager.is_authenticated() and credentials:
                        success, _ = await auth.auth_manager.open_session(credentials)
                        if not success:
                            result = safe_json_serialize({
                                "success": False,
                                "message": "Failed to authenticate with provided credentials",
                                "status": "authentication_failed",
                                "timestamp": datetime.now().isoformat()
                            })
                        else:
                            group_result = await group.create_group(
                                group_name=group_name, participants=participants
                            )
                            group_data = group_result.model_dump() if hasattr(group_result, 'model_dump') else group_result
                            group_data["success"] = True
                            group_data["timestamp"] = datetime.now().isoformat()
                            result = safe_json_serialize(group_data)
                    elif not auth.auth_manager.is_authenticated():
                        result = safe_json_serialize({
                            "success": False,
                            "message": "No active session. Please open a session first or provide credentials.",
                            "status": "no_session",
                            "timestamp": datetime.now().isoformat()
                        })
                    else:
                        group_result = await group.create_group(
                            group_name=group_name, participants=participants
                        )
                        group_data = group_result.model_dump() if hasattr(group_result, 'model_dump') else group_result
                        group_data["success"] = True
                        group_data["timestamp"] = datetime.now().isoformat()
                        result = safe_json_serialize(group_data)
            except Exception as e:
                logger.error(f"Error in create_group: {e}")
                result = safe_json_serialize({
                    "success": False,
                    "message": f"Failed to create group: {str(e)}",
                    "status": "error",
                    "timestamp": datetime.now().isoformat()
                })
                
        elif name == "get_group_participants":
            try:
                credentials = extract_credentials(arguments)
                group_id = arguments.get("group_id")
                
                # Validate required parameters
                if not group_id:
                    result = safe_json_serialize({
                        "success": False,
                        "message": "Missing required parameter: group_id",
                        "participants": [],
                        "status": "validation_error",
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    # Auto-authenticate if credentials provided and no session exists
                    if not auth.auth_manager.is_authenticated() and credentials:
                        success, _ = await auth.auth_manager.open_session(credentials)
                        if not success:
                            result = safe_json_serialize({
                                "success": False,
                                "message": "Failed to authenticate with provided credentials",
                                "participants": [],
                                "status": "authentication_failed",
                                "timestamp": datetime.now().isoformat()
                            })
                        else:
                            participants = await group.get_group_participants(group_id=group_id)
                            participants_data = [p.model_dump() if hasattr(p, 'model_dump') else p for p in participants]
                            result = safe_json_serialize({
                                "success": True,
                                "participants": participants_data,
                                "total": len(participants_data),
                                "group_id": group_id,
                                "status": "success",
                                "timestamp": datetime.now().isoformat()
                            })
                    elif not auth.auth_manager.is_authenticated():
                        result = safe_json_serialize({
                            "success": False,
                            "message": "No active session. Please open a session first or provide credentials.",
                            "participants": [],
                            "status": "no_session",
                            "timestamp": datetime.now().isoformat()
                        })
                    else:
                        participants = await group.get_group_participants(group_id=group_id)
                        participants_data = [p.model_dump() if hasattr(p, 'model_dump') else p for p in participants]
                        result = safe_json_serialize({
                            "success": True,
                            "participants": participants_data,
                            "total": len(participants_data),
                            "group_id": group_id,
                            "status": "success",
                            "timestamp": datetime.now().isoformat()
                        })
            except Exception as e:
                logger.error(f"Error in get_group_participants: {e}")
                result = safe_json_serialize({
                    "success": False,
                    "message": f"Failed to get group participants: {str(e)}",
                    "participants": [],
                    "status": "error",
                    "timestamp": datetime.now().isoformat()
                })
                
        elif name == "get_account_info":
            try:
                credentials = extract_credentials(arguments)
                
                # Auto-authenticate if credentials provided and no session exists
                if not auth.auth_manager.is_authenticated() and credentials:
                    success, _ = await auth.auth_manager.open_session(credentials)
                    if not success:
                        result = safe_json_serialize({
                            "success": False,
                            "message": "Failed to authenticate with provided credentials",
                            "account_info": None,
                            "status": "authentication_failed",
                            "timestamp": datetime.now().isoformat()
                        })
                    else:
                        client = auth.auth_manager.get_client()
                        if not client or not client.client:
                            result = safe_json_serialize({
                                "success": False,
                                "message": "No active WhatsApp client",
                                "account_info": None,
                                "status": "no_client",
                                "timestamp": datetime.now().isoformat()
                            })
                        else:
                            # Get account settings and state
                            settings_response = client.client.account.getSettings()
                            state_response = client.client.account.getStateInstance()
                            
                            account_info = {
                                "settings": settings_response,
                                "state": state_response,
                                "authenticated": client.is_authenticated,
                                "retrieved_at": datetime.now().isoformat()
                            }
                            result = safe_json_serialize({
                                "success": True,
                                "account_info": account_info,
                                "message": "Account information retrieved successfully",
                                "status": "success",
                                "timestamp": datetime.now().isoformat()
                            })
                elif not auth.auth_manager.is_authenticated():
                    result = safe_json_serialize({
                        "success": False,
                        "message": "No active session. Please open a session first or provide credentials.",
                        "account_info": None,
                        "status": "no_session",
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    client = auth.auth_manager.get_client()
                    if not client or not client.client:
                        result = safe_json_serialize({
                            "success": False,
                            "message": "No active WhatsApp client",
                            "account_info": None,
                            "status": "no_client",
                            "timestamp": datetime.now().isoformat()
                        })
                    else:
                        # Get account settings and state
                        settings_response = client.client.account.getSettings()
                        state_response = client.client.account.getStateInstance()
                        
                        account_info = {
                            "settings": settings_response,
                            "state": state_response,
                            "authenticated": client.is_authenticated,
                            "retrieved_at": datetime.now().isoformat()
                        }
                        result = safe_json_serialize({
                            "success": True,
                            "account_info": account_info,
                            "message": "Account information retrieved successfully",
                            "status": "success",
                            "timestamp": datetime.now().isoformat()
                        })
            except Exception as e:
                logger.error(f"Error in get_account_info: {e}")
                result = safe_json_serialize({
                    "success": False,
                    "message": f"Failed to get account info: {str(e)}",
                    "account_info": None,
                    "status": "error",
                    "timestamp": datetime.now().isoformat()
                })
        elif name == "get_chat_history":
            try:
                credentials = extract_credentials(arguments)
                chat_id = arguments.get("chat_id")
                count = arguments.get("count", 100)
                
                # Validate required parameters
                if not chat_id:
                    result = safe_json_serialize({
                        "success": False,
                        "message": "Missing required parameter: chat_id",
                        "messages": [],
                        "status": "validation_error",
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    # Validate count parameter
                    if not isinstance(count, int) or count <= 0:
                        count = 100
                    
                    # Auto-authenticate if credentials provided and no session exists
                    if not auth.auth_manager.is_authenticated() and credentials:
                        success, _ = await auth.auth_manager.open_session(credentials)
                        if not success:
                            result = safe_json_serialize({
                                "success": False,
                                "message": "Failed to authenticate with provided credentials",
                                "messages": [],
                                "status": "authentication_failed",
                                "timestamp": datetime.now().isoformat()
                            })
                        else:
                            messages = await message.get_chat_history(chat_id=chat_id, count=count)
                            result = safe_json_serialize({
                                "success": True,
                                "messages": messages,
                                "total": len(messages),
                                "chat_id": chat_id,
                                "count": count,
                                "status": "success",
                                "timestamp": datetime.now().isoformat()
                            })
                    elif not auth.auth_manager.is_authenticated():
                        result = safe_json_serialize({
                            "success": False,
                            "message": "No active session. Please open a session first or provide credentials.",
                            "messages": [],
                            "status": "no_session",
                            "timestamp": datetime.now().isoformat()
                        })
                    else:
                        messages = await message.get_chat_history(chat_id=chat_id, count=count)
                        result = safe_json_serialize({
                            "success": True,
                            "messages": messages,
                            "total": len(messages),
                            "chat_id": chat_id,
                            "count": count,
                            "status": "success",
                            "timestamp": datetime.now().isoformat()
                        })
            except Exception as e:
                logger.error(f"Error in get_chat_history: {e}")
                result = safe_json_serialize({
                    "success": False,
                    "message": f"Failed to get chat history: {str(e)}",
                    "messages": [],
                    "status": "error",
                    "timestamp": datetime.now().isoformat()
                })
        else:
            result = safe_json_serialize({
                "success": False,
                "message": f"Unknown tool '{name}'",
                "status": "unknown_tool",
                "available_tools": ["open_session", "close_session", "get_session_status", "send_message", "get_chats", "get_chat_history", "create_group", "get_group_participants", "get_account_info"],
                "timestamp": datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Critical error in tool '{name}': {e}")
        result = safe_json_serialize({
            "success": False,
            "message": f"Critical error: {str(e)}",
            "status": "critical_error",
            "tool_name": name,
            "timestamp": datetime.now().isoformat()
        })
    
    return [TextContent(type="text", text=result)]


async def main():
    """Main entry point for the WhatsApp MCP server."""
    logger.info("🚀 Starting WhatsApp MCP server...")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="whatsapp-mcp-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
