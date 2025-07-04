"""
TeamSpeak MCP Server - Allows controlling TeamSpeak from AI models.
"""

import argparse
import asyncio
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Sequence

import ts3
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
from pydantic import BaseModel

# Logging configuration - ensure all logs go to stderr for MCP protocol compliance
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="TeamSpeak MCP Server")
    parser.add_argument("--host", default=os.getenv("TEAMSPEAK_HOST", "localhost"),
                       help="TeamSpeak server host")
    parser.add_argument("--port", type=int, default=int(os.getenv("TEAMSPEAK_PORT", "10011")),
                       help="TeamSpeak ServerQuery port")
    parser.add_argument("--user", default=os.getenv("TEAMSPEAK_USER", "serveradmin"),
                       help="TeamSpeak ServerQuery username")
    parser.add_argument("--password", default=os.getenv("TEAMSPEAK_PASSWORD", ""),
                       help="TeamSpeak ServerQuery password")
    parser.add_argument("--server-id", type=int, default=int(os.getenv("TEAMSPEAK_SERVER_ID", "1")),
                       help="TeamSpeak virtual server ID")
    return parser.parse_args()

class TeamSpeakConnection:
    """TeamSpeak connection manager."""
    
    def __init__(self, host=None, port=None, user=None, password=None, server_id=None):
        # Use provided arguments or fall back to environment variables
        self.connection: Optional[ts3.query.TS3Connection] = None
        self.host = host or os.getenv("TEAMSPEAK_HOST", "localhost")
        self.port = port or int(os.getenv("TEAMSPEAK_PORT", "10011"))
        self.user = user or os.getenv("TEAMSPEAK_USER", "serveradmin")
        self.password = password or os.getenv("TEAMSPEAK_PASSWORD", "")
        self.server_id = server_id or int(os.getenv("TEAMSPEAK_SERVER_ID", "1"))
        
    async def connect(self) -> bool:
        """Connect to TeamSpeak server."""
        try:
            # Use asyncio.to_thread for blocking operations
            self.connection = await asyncio.to_thread(ts3.query.TS3Connection, self.host, self.port)
            await asyncio.to_thread(self.connection.use, sid=self.server_id)
            
            # Authenticate if password is provided
            if self.password:
                # First try to login with username/password (classic ServerQuery auth)
                try:
                    await asyncio.to_thread(self.connection.login, client_login_name=self.user, client_login_password=self.password)
                    logger.info("Successfully authenticated with username/password")
                except Exception as login_error:
                    logger.info(f"Username/password authentication failed: {login_error}")
                    
                    # If login fails, try to use as admin token
                    try:
                        await asyncio.to_thread(self.connection.tokenuse, token=self.password)
                        logger.info("Successfully used admin privilege key")
                    except Exception as token_error:
                        logger.warning(f"Could not use admin token either: {token_error}")
                        logger.warning("Continuing with basic anonymous permissions")
            else:
                logger.info("No password provided, using anonymous connection")
            
            # Test basic connectivity and permissions
            try:
                # Try a simple command to verify permissions
                await asyncio.to_thread(self.connection.whoami)
                logger.info("Basic connectivity test passed")
            except Exception as test_error:
                logger.warning(f"Basic connectivity test failed: {test_error}")
            
            logger.info("TeamSpeak connection established successfully")
            return True
        except Exception as e:
            logger.error(f"TeamSpeak connection error: {e}")
            self.connection = None
            return False
    
    async def disconnect(self):
        """Disconnect from TeamSpeak server."""
        if self.connection:
            try:
                await asyncio.to_thread(self.connection.quit)
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
            finally:
                self.connection = None
                logger.info("TeamSpeak disconnected")
    
    def is_connected(self) -> bool:
        """Check if connection is active."""
        return self.connection is not None


def get_connection_from_args(args: dict = None) -> 'TeamSpeakConnection':
    """Get TeamSpeak connection from dynamic credentials or use global connection."""
    if args and "teamspeak_credentials" in args:
        creds = args["teamspeak_credentials"]
        return TeamSpeakConnection(
            host=creds.get("host", "localhost"),
            port=int(creds.get("port", "10011")),
            user=creds.get("user", "serveradmin"),
            password=creds.get("password", ""),
            server_id=int(creds.get("server_id", "1"))
        )
    else:
        return ts_connection

# Global connection instance - will be initialized in main()
ts_connection = None

# MCP Tools definition
TOOLS = [
    Tool(
        name="connect_to_server",
        description="Connect to the configured TeamSpeak server",
        inputSchema={
            "type": "object",
            "properties": {
            },
            "additionalProperties": True,
        },
    ),
    Tool(
        name="send_channel_message",
        description="Send a message to a TeamSpeak channel",
        inputSchema={
            "type": "object",
            "properties": {
                "channel_id": {
                    "type": "integer",
                    "description": "Channel ID (optional, uses current channel if not specified)",
                },
                "message": {
                    "type": "string",
                    "description": "Message to send",
                },
            },
            "required": ["message"],
            "additionalProperties": True,
        },
    ),
    Tool(
        name="send_private_message",
        description="Send a private message to a user",
        inputSchema={
            "type": "object",
            "properties": {
                "client_id": {
                    "type": "integer",
                    "description": "Target client ID",
                },
                "message": {
                    "type": "string",
                    "description": "Message to send",
                },
            },
            "required": ["client_id", "message"],
            "additionalProperties": True,
        },
    ),
    Tool(
        name="poke_client",
        description="Send a poke (alert notification) to a client - more attention-grabbing than a private message",
        inputSchema={
            "type": "object",
            "properties": {
                "client_id": {
                    "type": "integer",
                    "description": "Target client ID to poke",
                },
                "message": {
                    "type": "string",
                    "description": "Poke message to send",
                },
            },
            "required": ["client_id", "message"],
            "additionalProperties": True,
        },
    ),
    Tool(
        name="list_clients",
        description="List all clients connected to the server",
        inputSchema={
            "type": "object",
            "properties": {
            },
            "additionalProperties": True,
        },
    ),
    Tool(
        name="list_channels",
        description="List all channels on the server",
        inputSchema={
            "type": "object",
            "properties": {
            },
            "additionalProperties": True,
        },
    ),
    Tool(
        name="create_channel",
        description="Create a new channel",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Channel name",
                },
                "parent_id": {
                    "type": "integer",
                    "description": "Parent channel ID (optional)",
                },
                "permanent": {
                    "type": "boolean",
                    "description": "Permanent or temporary channel (default: temporary)",
                    "default": False,
                },
            },
            "required": ["name"],
            "additionalProperties": True,
        },
    ),
    Tool(
        name="delete_channel",
        description="Delete a channel",
        inputSchema={
            "type": "object",
            "properties": {
                "channel_id": {
                    "type": "integer",
                    "description": "Channel ID to delete",
                },
                "force": {
                    "type": "boolean",
                    "description": "Force deletion even if clients are present",
                    "default": False,
                },
            },
            "required": ["channel_id"],
            "additionalProperties": True,
        },
    ),
    Tool(
        name="move_client",
        description="Move a client to another channel",
        inputSchema={
            "type": "object",
            "properties": {
                "client_id": {
                    "type": "integer",
                    "description": "Client ID",
                },
                "channel_id": {
                    "type": "integer",
                    "description": "Destination channel ID",
                },
            },
            "required": ["client_id", "channel_id"],
            "additionalProperties": True,
        },
    ),
    Tool(
        name="kick_client",
        description="Kick a client from server or channel",
        inputSchema={
            "type": "object",
            "properties": {
                "client_id": {
                    "type": "integer",
                    "description": "Client ID",
                },
                "reason": {
                    "type": "string",
                    "description": "Kick reason",
                    "default": "Expelled by AI",
                },
                "from_server": {
                    "type": "boolean",
                    "description": "Kick from server (true) or channel (false)",
                    "default": False,
                },
            },
            "required": ["client_id"],
            "additionalProperties": True,
        },
    ),
    Tool(
        name="ban_client",
        description="Ban a client from the server",
        inputSchema={
            "type": "object",
            "properties": {
                "client_id": {
                    "type": "integer",
                    "description": "Client ID",
                },
                "reason": {
                    "type": "string",
                    "description": "Ban reason",
                    "default": "Banned by AI",
                },
                "duration": {
                    "type": "integer",
                    "description": "Ban duration in seconds (0 = permanent)",
                    "default": 0,
                },
            },
            "required": ["client_id"],
            "additionalProperties": True,
        },
    ),
    Tool(
        name="server_info",
        description="Get TeamSpeak server information",
        inputSchema={
            "type": "object",
            "properties": {
            },
            "additionalProperties": True,
        },
    ),
    Tool(
        name="update_channel",
        description="Update channel properties (name, description, password, talk power, limits, etc.)",
        inputSchema={
            "type": "object",
            "properties": {
                "channel_id": {
                    "type": "integer",
                    "description": "Channel ID to update",
                },
                "name": {
                    "type": "string",
                    "description": "New channel name (optional)",
                },
                "description": {
                    "type": "string",
                    "description": "New channel description (optional)",
                },
                "password": {
                    "type": "string",
                    "description": "New channel password (optional, empty string to remove)",
                },
                "max_clients": {
                    "type": "integer",
                    "description": "Maximum number of clients (optional)",
                },
                "talk_power": {
                    "type": "integer",
                    "description": "Required talk power to speak in channel (optional)",
                },
                "codec_quality": {
                    "type": "integer",
                    "description": "Audio codec quality 1-10 (optional)",
                },
                "permanent": {
                    "type": "boolean",
                    "description": "Make channel permanent (optional)",
                },
            },
            "required": ["channel_id"],
            "additionalProperties": True,
        },
    ),
    Tool(
        name="set_channel_talk_power",
        description="Set talk power requirement for a channel (useful for AFK/silent channels)",
        inputSchema={
            "type": "object",
            "properties": {
                "channel_id": {
                    "type": "integer",
                    "description": "Channel ID to configure",
                },
                "talk_power": {
                    "type": "integer",
                    "description": "Required talk power (0=everyone can talk, 999=silent channel)",
                },
                "preset": {
                    "type": "string",
                    "description": "Quick preset: 'silent' (999), 'moderated' (50), 'normal' (0)",
                    "enum": ["silent", "moderated", "normal"],
                },
            },
            "required": ["channel_id"],
            "additionalProperties": True,
        },
    ),
    Tool(
        name="channel_info",
        description="Get detailed information about a specific channel",
        inputSchema={
            "type": "object",
            "properties": {
                "channel_id": {
                    "type": "integer",
                    "description": "Channel ID to get info for",
                },
            },
            "required": ["channel_id"],
            "additionalProperties": True,
        },
    ),
    Tool(
        name="manage_channel_permissions",
        description="Add or remove specific permissions for a channel",
        inputSchema={
            "type": "object",
            "properties": {
                "channel_id": {
                    "type": "integer",
                    "description": "Channel ID to modify permissions for",
                },
                "action": {
                    "type": "string",
                    "description": "Action to perform",
                    "enum": ["add", "remove", "list"],
                },
                "permission": {
                    "type": "string",
                    "description": "Permission name (required for add/remove actions)",
                },
                "value": {
                    "type": "integer",
                    "description": "Permission value (required for add action)",
                },
            },
            "required": ["channel_id", "action"],
            "additionalProperties": True,
        },
    ),
    Tool(
        name="client_info_detailed",
        description="Get detailed information about a specific client",
        inputSchema={
            "type": "object",
            "properties": {
                "client_id": {
                    "type": "integer",
                    "description": "Client ID to get detailed info for",
                },
            },
            "required": ["client_id"],
            "additionalProperties": True,
        },
    ),
    Tool(
        name="update_server_settings",
        description="Update virtual server settings (name, welcome message, max clients, etc.)",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Server name (optional)",
                },
                "welcome_message": {
                    "type": "string",
                    "description": "Server welcome message (optional)",
                },
                "max_clients": {
                    "type": "integer",
                    "description": "Maximum number of clients (optional)",
                },
                "password": {
                    "type": "string",
                    "description": "Server password (optional, empty string to remove)",
                },
                "hostmessage": {
                    "type": "string",
                    "description": "Host message displayed in server info (optional)",
                },
                "hostmessage_mode": {
                    "type": "integer",
                    "description": "Host message mode: 0=none, 1=log, 2=modal, 3=modalquit (optional)",
                },
                "default_server_group": {
                    "type": "integer",
                    "description": "Default server group ID for new clients (optional)",
                },
                "default_channel_group": {
                    "type": "integer", 
                    "description": "Default channel group ID for new clients (optional)",
                },
            },
            "required": [],
            "additionalProperties": True,
        },
    ),
    Tool(
        name="manage_user_permissions",
        description="Manage user permissions: add/remove server groups, set individual permissions",
        inputSchema={
            "type": "object",
            "properties": {
                "client_id": {
                    "type": "integer",
                    "description": "Client ID to manage permissions for",
                },
                "action": {
                    "type": "string",
                    "description": "Action to perform",
                    "enum": ["add_group", "remove_group", "list_groups", "add_permission", "remove_permission", "list_permissions"],
                },
                "group_id": {
                    "type": "integer",
                    "description": "Server group ID (required for add_group/remove_group actions)",
                },
                "permission": {
                    "type": "string",
                    "description": "Permission name (required for add_permission/remove_permission actions)",
                },
                "value": {
                    "type": "integer",
                    "description": "Permission value (required for add_permission action)",
                },
                "skip": {
                    "type": "boolean",
                    "description": "Skip flag for permission (optional, default: false)",
                    "default": False,
                },
                "negate": {
                    "type": "boolean",
                    "description": "Negate flag for permission (optional, default: false)",
                    "default": False,
                },
            },
            "required": ["client_id", "action"],
            "additionalProperties": True,
        },
    ),
    Tool(
        name="diagnose_permissions",
        description="Diagnose current connection permissions and provide troubleshooting help",
        inputSchema={
            "type": "object",
            "properties": {
            },
            "additionalProperties": True,
        },
    ),
    # Nouveaux outils - Gestion des groupes serveur
    Tool(
        name="list_server_groups",
        description="List all server groups available on the virtual server",
        inputSchema={
            "type": "object",
            "properties": {
            },
            "additionalProperties": True,
        },
    ),
    Tool(
        name="assign_client_to_group",
        description="Add or remove a client from a server group",
        inputSchema={
            "type": "object",
            "properties": {
                "client_database_id": {
                    "type": "integer",
                    "description": "Client database ID to modify group membership for",
                },
                "action": {
                    "type": "string",
                    "description": "Action to perform",
                    "enum": ["add", "remove"],
                },
                "group_id": {
                    "type": "integer",
                    "description": "Server group ID to add/remove client from",
                },
            },
            "required": ["client_database_id", "action", "group_id"],
            "additionalProperties": True,
        },
    ),
    Tool(
        name="create_server_group",
        description="Create a new server group with specified name and type",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name for the new server group",
                },
                "type": {
                    "type": "integer",
                    "description": "Group type (0=template, 1=regular, 2=query, default: 1)",
                    "default": 1,
                },
            },
            "required": ["name"],
            "additionalProperties": True,
        },
    ),
    Tool(
        name="manage_server_group_permissions",
        description="Add, remove or list permissions for a server group",
        inputSchema={
            "type": "object",
            "properties": {
                "group_id": {
                    "type": "integer",
                    "description": "Server group ID to modify permissions for",
                },
                "action": {
                    "type": "string",
                    "description": "Action to perform",
                    "enum": ["add", "remove", "list"],
                },
                "permission": {
                    "type": "string",
                    "description": "Permission name (required for add/remove actions)",
                },
                "value": {
                    "type": "integer",
                    "description": "Permission value (required for add action)",
                },
                "skip": {
                    "type": "boolean",
                    "description": "Skip flag for permission (optional, default: false)",
                    "default": False,
                },
                "negate": {
                    "type": "boolean",
                    "description": "Negate flag for permission (optional, default: false)",
                    "default": False,
                },
            },
            "required": ["group_id", "action"],
            "additionalProperties": True,
        },
    ),
    # Nouveaux outils - Gestion des bans et modération
    Tool(
        name="list_bans",
        description="List all active ban rules on the virtual server",
        inputSchema={
            "type": "object",
            "properties": {
            },
            "additionalProperties": True,
        },
    ),
    Tool(
        name="manage_ban_rules",
        description="Create, delete or manage ban rules",
        inputSchema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform",
                    "enum": ["add", "delete", "delete_all"],
                },
                "ban_id": {
                    "type": "integer",
                    "description": "Ban ID (required for delete action)",
                },
                "ip": {
                    "type": "string",
                    "description": "IP address pattern to ban (optional for add action)",
                },
                "name": {
                    "type": "string",
                    "description": "Name pattern to ban (optional for add action)",
                },
                "uid": {
                    "type": "string",
                    "description": "Client unique identifier to ban (optional for add action)",
                },
                "time": {
                    "type": "integer",
                    "description": "Ban duration in seconds (0 = permanent, default: 0)",
                    "default": 0,
                },
                "reason": {
                    "type": "string",
                    "description": "Ban reason (optional)",
                    "default": "Banned by AI",
                },
            },
            "required": ["action"],
            "additionalProperties": True,
        },
    ),
    Tool(
        name="list_complaints",
        description="List complaints on the virtual server",
        inputSchema={
            "type": "object",
            "properties": {
                "target_client_database_id": {
                    "type": "integer",
                    "description": "Target client database ID to filter complaints (optional)",
                },
            },
            "required": [],
            "additionalProperties": True,
        },
    ),
    # Nouveaux outils - Recherche et utilitaires
    Tool(
        name="search_clients",
        description="Search for clients by name pattern or unique identifier",
        inputSchema={
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Search pattern for client name or UID",
                },
                "search_by_uid": {
                    "type": "boolean",
                    "description": "Search by unique identifier instead of name (default: false)",
                    "default": False,
                },
            },
            "required": ["pattern"],
            "additionalProperties": True,
        },
    ),
    Tool(
        name="find_channels",
        description="Search for channels by name pattern",
        inputSchema={
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Search pattern for channel name",
                },
            },
            "required": ["pattern"],
            "additionalProperties": True,
        },
    ),
    # Nouveaux outils - Tokens et privilèges
    Tool(
        name="list_privilege_tokens",
        description="List all privilege keys/tokens available on the server",
        inputSchema={
            "type": "object",
            "properties": {
            },
            "additionalProperties": True,
        },
    ),
    Tool(
        name="create_privilege_token",
        description="Create a new privilege key/token for server or channel group access",
        inputSchema={
            "type": "object",
            "properties": {
                "token_type": {
                    "type": "integer",
                    "description": "Token type (0=server group, 1=channel group)",
                    "enum": [0, 1],
                },
                "group_id": {
                    "type": "integer",
                    "description": "Server group ID (for token_type=0) or channel group ID (for token_type=1)",
                },
                "channel_id": {
                    "type": "integer",
                    "description": "Channel ID (required for channel group tokens when token_type=1)",
                },
                "description": {
                    "type": "string",
                    "description": "Optional description for the token",
                },
                "custom_set": {
                    "type": "string",
                    "description": "Optional custom client properties set (format: ident=value|ident=value)",
                },
            },
            "required": ["token_type", "group_id"],
            "additionalProperties": True,
        },
    ),
    # Nouveaux outils - Transfert de fichiers
    Tool(
        name="list_files",
        description="List files in a channel's file repository",
        inputSchema={
            "type": "object",
            "properties": {
                "channel_id": {
                    "type": "integer",
                    "description": "Channel ID to list files for",
                },
                "path": {
                    "type": "string",
                    "description": "Directory path to list (default: root '/')",
                    "default": "/",
                },
                "channel_password": {
                    "type": "string",
                    "description": "Channel password if required (optional)",
                },
            },
            "required": ["channel_id"],
            "additionalProperties": True,
        },
    ),
    Tool(
        name="get_file_info",
        description="Get detailed information about a specific file in a channel",
        inputSchema={
            "type": "object",
            "properties": {
                "channel_id": {
                    "type": "integer",
                    "description": "Channel ID containing the file",
                },
                "file_path": {
                    "type": "string",
                    "description": "Full path to the file",
                },
                "channel_password": {
                    "type": "string",
                    "description": "Channel password if required (optional)",
                },
            },
            "required": ["channel_id", "file_path"],
            "additionalProperties": True,
        },
    ),
    Tool(
        name="manage_file_permissions",
        description="List active file transfers and manage file transfer permissions",
        inputSchema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform",
                    "enum": ["list_transfers", "stop_transfer"],
                },
                "transfer_id": {
                    "type": "integer",
                    "description": "File transfer ID (required for stop_transfer action)",
                },
                "delete_partial": {
                    "type": "boolean",
                    "description": "Delete partial file when stopping transfer (default: false)",
                    "default": False,
                },
            },
            "required": ["action"],
            "additionalProperties": True,
        },
    ),
    # Nouveaux outils - Logs et monitoring
    Tool(
        name="view_server_logs",
        description="View recent entries from the virtual server log with enhanced options",
        inputSchema={
            "type": "object",
            "properties": {
                "lines": {
                    "type": "integer",
                    "description": "Number of log lines to retrieve (1-100, default: 50)",
                    "default": 50,
                    "minimum": 1,
                    "maximum": 100,
                },
                "reverse": {
                    "type": "boolean",
                    "description": "Show logs in reverse order (newest first, default: true)",
                    "default": True,
                },
                "instance_log": {
                    "type": "boolean",
                    "description": "Show instance log instead of virtual server log (default: false)",
                    "default": False,
                },
                "begin_pos": {
                    "type": "integer",
                    "description": "Starting position in log file (optional)",
                },
                "log_level": {
                    "type": "integer",
                    "description": "Log level (1=ERROR, 2=WARNING, 3=DEBUG, 4=INFO)",
                    "enum": [1, 2, 3, 4],
                },
                "timestamp_from": {
                    "type": "integer",
                    "description": "Unix timestamp for log entries from (optional)",
                },
                "timestamp_to": {
                    "type": "integer",
                    "description": "Unix timestamp for log entries to (optional)",
                },
                "complete_mode": {
                    "type": "boolean",
                    "description": "Enable complete mode - retrieve ALL logs by paginating automatically (default: false)",
                    "default": False,
                },
                "max_iterations": {
                    "type": "integer",
                    "description": "Maximum pagination iterations in complete mode (default: 1000, protection against infinite loops)",
                    "default": 1000,
                    "minimum": 1,
                    "maximum": 10000,
                },
                "enhanced_debug": {
                    "type": "boolean",
                    "description": "Enable enhanced debugging information (default: false)",
                    "default": False,
                },
            },
            "required": [],
            "additionalProperties": True,
        },
    ),
    Tool(
        name="add_log_entry",
        description="Add a custom entry to the server log",
        inputSchema={
            "type": "object",
            "properties": {
                "log_level": {
                    "type": "integer",
                    "description": "Log level (1=ERROR, 2=WARNING, 3=DEBUG, 4=INFO)",
                    "enum": [1, 2, 3, 4],
                },
                "message": {
                    "type": "string",
                    "description": "Log message to add",
                },
            },
            "required": ["log_level", "message"],
            "additionalProperties": True,
        },
    ),
    Tool(
        name="get_connection_info",
        description="Get detailed connection information for the virtual server",
        inputSchema={
            "type": "object",
            "properties": {
            },
            "additionalProperties": True,
        },
    ),
    # Nouveaux outils - Snapshots et backup
    Tool(
        name="create_server_snapshot",
        description="Create a snapshot of the virtual server configuration",
        inputSchema={
            "type": "object",
            "properties": {
            },
            "additionalProperties": True,
        },
    ),
    Tool(
        name="deploy_server_snapshot",
        description="Deploy/restore a server configuration from a snapshot",
        inputSchema={
            "type": "object",
            "properties": {
                "snapshot_data": {
                    "type": "string",
                    "description": "Snapshot data to deploy (from create_server_snapshot)",
                },
            },
            "required": ["snapshot_data"],
            "additionalProperties": True,
        },
    ),
    Tool(
        name="get_instance_logs",
        description="Get instance-level logs instead of virtual server logs",
        inputSchema={
            "type": "object",
            "properties": {
                "lines": {
                    "type": "integer",
                    "description": "Number of log lines to retrieve (1-100, default: 50)",
                    "default": 50,
                    "minimum": 1,
                    "maximum": 100,
                },
                "reverse": {
                    "type": "boolean",
                    "description": "Show logs in reverse order (newest first, default: true)",
                    "default": True,
                },
                "begin_pos": {
                    "type": "integer",
                    "description": "Starting position in log file (optional)",
                },
            },
            "required": [],
            "additionalProperties": True,
        },
    ),
]

class TeamSpeakMCPServer:
    """TeamSpeak MCP Server class for backward compatibility with tests."""
    
    def __init__(self):
        self.tools = TOOLS
    
    async def handle_list_tools(self, request) -> ListToolsResult:
        """Handle list tools request."""
        return ListToolsResult(tools=self.tools)

async def run_server():
    """Run the MCP server."""
    global ts_connection
    
    # Parse command line arguments
    args = parse_args()
    
    # Initialize connection with default values (will be overridden by dynamic credentials)
    ts_connection = TeamSpeakConnection()
    
    # Create server instance
    server = Server("teamspeak-mcp")
    
    @server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        """Return list of available tools."""
        return TOOLS
    
    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Execute a requested tool."""
        try:
            if name == "connect_to_server":
                return await _connect_to_server(arguments)
            elif name == "send_channel_message":
                return await _send_channel_message(arguments)
            elif name == "send_private_message":
                return await _send_private_message(arguments)
            elif name == "poke_client":
                return await _poke_client(arguments)
            elif name == "list_clients":
                return await _list_clients(arguments)
            elif name == "list_channels":
                return await _list_channels(arguments)
            elif name == "create_channel":
                return await _create_channel(arguments)
            elif name == "delete_channel":
                return await _delete_channel(arguments)
            elif name == "move_client":
                return await _move_client(arguments)
            elif name == "kick_client":
                return await _kick_client(arguments)
            elif name == "ban_client":
                return await _ban_client(arguments)
            elif name == "server_info":
                return await _server_info(arguments)
            elif name == "update_channel":
                return await _update_channel(arguments)
            elif name == "set_channel_talk_power":
                return await _set_channel_talk_power(arguments)
            elif name == "channel_info":
                return await _channel_info(arguments)
            elif name == "manage_channel_permissions":
                return await _manage_channel_permissions(arguments)
            elif name == "client_info_detailed":
                return await _client_info_detailed(arguments)
            elif name == "update_server_settings":
                return await _update_server_settings(arguments)
            elif name == "manage_user_permissions":
                return await _manage_user_permissions(arguments)
            elif name == "diagnose_permissions":
                return await _diagnose_permissions(arguments)
            elif name == "list_server_groups":
                return await _list_server_groups(arguments)
            elif name == "assign_client_to_group":
                return await _assign_client_to_group(arguments)
            elif name == "create_server_group":
                return await _create_server_group(arguments)
            elif name == "manage_server_group_permissions":
                return await _manage_server_group_permissions(arguments)
            elif name == "list_bans":
                return await _list_bans(arguments)
            elif name == "manage_ban_rules":
                return await _manage_ban_rules(arguments)
            elif name == "list_complaints":
                return await _list_complaints(arguments)
            elif name == "search_clients":
                return await _search_clients(arguments)
            elif name == "find_channels":
                return await _find_channels(arguments)
            elif name == "list_privilege_tokens":
                return await _list_privilege_tokens(arguments)
            elif name == "create_privilege_token":
                return await _create_privilege_token(arguments)
            elif name == "list_files":
                return await _list_files(arguments)
            elif name == "get_file_info":
                return await _get_file_info(arguments)
            elif name == "manage_file_permissions":
                return await _manage_file_permissions(arguments)
            elif name == "view_server_logs":
                return await _view_server_logs(arguments)
            elif name == "add_log_entry":
                return await _add_log_entry(arguments)
            elif name == "get_connection_info":
                return await _get_connection_info(arguments)
            elif name == "create_server_snapshot":
                return await _create_server_snapshot(arguments)
            elif name == "deploy_server_snapshot":
                return await _deploy_server_snapshot(arguments)
            elif name == "get_instance_logs":
                return await _get_instance_logs(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
        except Exception as e:
            raise Exception(f"Error: {str(e)}")
    
    logger.info("🚀 Starting TeamSpeak MCP server...")
    logger.info(f"Host: {ts_connection.host}:{ts_connection.port}")
    logger.info(f"User: {ts_connection.user}")
    logger.info(f"Server ID: {ts_connection.server_id}")
    
    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="teamspeak",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    finally:
        if ts_connection:
            await ts_connection.disconnect()

async def _connect_to_server(args: dict = None) -> list[TextContent]:
    """Connect to TeamSpeak server."""
    
    # Create a new connection with dynamic credentials if provided
    connection = None
    if args and "teamspeak_credentials" in args:
        creds = args["teamspeak_credentials"]
        connection = TeamSpeakConnection(
            host=creds.get("host", "localhost"),
            port=int(creds.get("port", "10011")),
            user=creds.get("user", "serveradmin"),
            password=creds.get("password", ""),
            server_id=int(creds.get("server_id", "1"))
        )
    else:
        # Use global connection as fallback
        connection = ts_connection

    try:
        success = await connection.connect()
        if success:
            return [TextContent(type="text", text="✅ TeamSpeak server connection successful")]
        else:
            # Provide detailed diagnostic information
            diagnostic_info = f"""❌ TeamSpeak server connection failed

🔍 **Connection Details:**
- Host: {connection.host}
- Port: {connection.port}
- User: {connection.user}
- Password: {'[SET]' if connection.password else '[NOT SET]'}
- Server ID: {connection.server_id}

🛠️ **Troubleshooting Steps:**
1. **Check if TeamSpeak server is running** on {connection.host}:{connection.port}
2. **Verify ServerQuery is enabled** in TeamSpeak server settings
3. **Check firewall** - ensure port {connection.port} is accessible
4. **Verify credentials** - ensure the password/privilege key is correct
5. **Test with telnet**: `telnet {connection.host} {connection.port}`

💡 **Common Issues:**
- TeamSpeak server not running
- ServerQuery disabled in server settings
- Wrong port (default ServerQuery port is 10011)
- Invalid privilege key or password
- Firewall blocking connection"""
            
            return [TextContent(type="text", text=diagnostic_info)]
    except Exception as e:
        error_info = f"""❌ TeamSpeak connection error: {str(e)}

🔍 **Connection Details:**
- Host: {connection.host}
- Port: {connection.port}
- Error: {type(e).__name__}: {str(e)}

🛠️ **Possible Solutions:**
1. Check if TeamSpeak server is running
2. Verify ServerQuery is enabled
3. Check network connectivity
4. Verify credentials are correct"""
        
        return [TextContent(type="text", text=error_info)]

async def _send_channel_message(args: dict) -> list[TextContent]:
    """Send message to a channel."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    message = args["message"]
    channel_id = args.get("channel_id")
    
    try:
        if channel_id:
            await asyncio.to_thread(
                connection.connection.sendtextmessage,
                targetmode=2, target=channel_id, msg=message
            )
        else:
            await asyncio.to_thread(
                connection.connection.sendtextmessage,
                targetmode=2, target=0, msg=message
            )
        
        return [TextContent(type="text", text=f"✅ Message sent to channel: {message}")]
    except Exception as e:
        raise Exception(f"Error sending message: {e}")

async def _send_private_message(args: dict) -> list[TextContent]:
    """Send private message."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    client_id = args["client_id"]
    message = args["message"]
    
    try:
        await asyncio.to_thread(
            connection.connection.sendtextmessage,
            targetmode=1, target=client_id, msg=message
        )
        
        return [TextContent(type="text", text=f"✅ Private message sent to client {client_id}: {message}")]
    except Exception as e:
        raise Exception(f"Error sending private message: {e}")

async def _poke_client(args: dict) -> list[TextContent]:
    """Send a poke (alert notification) to a client."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    client_id = args["client_id"]
    message = args["message"]
    
    try:
        await asyncio.to_thread(
            connection.connection.clientpoke,
            clid=client_id, msg=message
        )
        
        return [TextContent(type="text", text=f"👉 Poke sent to client {client_id}: {message}")]
    except Exception as e:
        raise Exception(f"Error sending poke: {e}")

async def _list_clients(args: dict = None) -> list[TextContent]:
    """List connected clients."""
    
    # Get connection with dynamic credentials
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    try:
        response = await asyncio.to_thread(connection.connection.clientlist)
        
        # Extract clients list - response.parsed is a list of dictionaries
        if hasattr(response, 'parsed'):
            clients = response.parsed
        else:
            # Fallback to container emulation
            clients = list(response)
        
        result = "👥 **Connected clients:**\n\n"
        for client in clients:
            client_id = client.get('clid', 'N/A')
            nickname = client.get('client_nickname', 'N/A')
            channel_id = client.get('cid', 'N/A')
            result += f"• **ID {client_id}**: {nickname} (Channel: {channel_id})\n"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        error_message = str(e)
        
        # Check for specific permission errors
        if "error id 2568" in error_message or "insufficient client permissions" in error_message:
            diagnostic_result = "❌ **Erreur de permissions insuffisantes**\n\n"
            diagnostic_result += "La commande `list_clients` nécessite des permissions élevées.\n\n"
            diagnostic_result += "**🔧 Solutions possibles :**\n\n"
            diagnostic_result += "1. **Vérifiez votre mot de passe :**\n"
            diagnostic_result += "   - Utilisez un mot de passe ServerQuery valide\n"
            diagnostic_result += "   - Ou utilisez un token admin (commençant par 'token=')\n\n"
            diagnostic_result += "2. **Créez un utilisateur ServerQuery :**\n"
            diagnostic_result += "   ```\n"
            diagnostic_result += "   # Connectez-vous au ServerQuery\n"
            diagnostic_result += "   serverqueryadd client_login_name=mcp_user client_login_password=votre_mot_de_passe\n"
            diagnostic_result += "   servergroupaddclient sgid=6 cldbid=ID_USER  # Groupe Server Admin\n"
            diagnostic_result += "   ```\n\n"
            diagnostic_result += "3. **Obtenez un token admin :**\n"
            diagnostic_result += "   - Regardez les logs du serveur TS3 au démarrage\n"
            diagnostic_result += "   - Ou utilisez: `tokenadd tokentype=0 tokenid1=6`\n\n"
            diagnostic_result += "4. **Vérifiez la configuration :**\n"
            diagnostic_result += f"   - Host: {connection.host}\n"
            diagnostic_result += f"   - User: {connection.user}\n"
            diagnostic_result += f"   - Password: {'[SET]' if connection.password else '[NOT SET]'}\n\n"
            diagnostic_result += "**🔍 Test rapide :**\n"
            diagnostic_result += "Essayez d'abord avec `server_info` qui nécessite moins de permissions."
            
            return [TextContent(type="text", text=diagnostic_result)]
        else:
            raise Exception(f"Error retrieving clients: {e}")

async def _list_channels(args: dict = None) -> list[TextContent]:
    """List channels."""
    
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    try:
        response = await asyncio.to_thread(connection.connection.channellist)
        
        # Extract channels list - response.parsed is a list of dictionaries
        if hasattr(response, 'parsed'):
            channels = response.parsed
        else:
            # Fallback to container emulation
            channels = list(response)
        
        result = "📋 **Available channels:**\n\n"
        for channel in channels:
            channel_id = channel.get('cid', 'N/A')
            channel_name = channel.get('channel_name', 'N/A')
            result += f"• **ID {channel_id}**: {channel_name}\n"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error retrieving channels: {e}")

async def _create_channel(args: dict) -> list[TextContent]:
    """Create a new channel."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    name = args["name"]
    parent_id = args.get("parent_id", 0)
    permanent = args.get("permanent", False)
    
    try:
        channel_type = 1 if permanent else 0
        result = await asyncio.to_thread(
            connection.connection.channelcreate,
            channel_name=name,
            channel_flag_permanent=permanent,
            cpid=parent_id
        )
        
        return [TextContent(type="text", text=f"✅ Channel '{name}' created successfully")]
    except Exception as e:
        raise Exception(f"Error creating channel: {e}")

async def _delete_channel(args: dict) -> list[TextContent]:
    """Delete a channel."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    channel_id = args["channel_id"]
    force = args.get("force", False)
    
    try:
        await asyncio.to_thread(
            connection.connection.channeldelete,
            cid=channel_id, force=1 if force else 0
        )
        
        return [TextContent(type="text", text=f"✅ Channel {channel_id} deleted successfully")]
    except Exception as e:
        raise Exception(f"Error deleting channel: {e}")

async def _move_client(args: dict) -> list[TextContent]:
    """Move a client."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    client_id = args["client_id"]
    channel_id = args["channel_id"]
    
    try:
        await asyncio.to_thread(
            connection.connection.clientmove,
            clid=client_id, cid=channel_id
        )
        
        return [TextContent(type="text", text=f"✅ Client {client_id} moved to channel {channel_id}")]
    except Exception as e:
        raise Exception(f"Error moving client: {e}")

async def _kick_client(args: dict) -> list[TextContent]:
    """Kick a client."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    client_id = args["client_id"]
    reason = args.get("reason", "Expelled by AI")
    from_server = args.get("from_server", False)
    
    try:
        kick_type = 5 if from_server else 4  # 5 = server, 4 = channel
        await asyncio.to_thread(
            connection.connection.clientkick,
            clid=client_id, reasonid=kick_type, reasonmsg=reason
        )
        
        location = "from server" if from_server else "from channel"
        return [TextContent(type="text", text=f"✅ Client {client_id} kicked {location}: {reason}")]
    except Exception as e:
        raise Exception(f"Error kicking client: {e}")

async def _ban_client(args: dict) -> list[TextContent]:
    """Ban a client."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    client_id = args["client_id"]
    reason = args.get("reason", "Banned by AI")
    duration = args.get("duration", 0)
    
    try:
        await asyncio.to_thread(
            connection.connection.banclient,
            clid=client_id, time=duration, banreason=reason
        )
        
        duration_text = "permanently" if duration == 0 else f"for {duration} seconds"
        return [TextContent(type="text", text=f"✅ Client {client_id} banned {duration_text}: {reason}")]
    except Exception as e:
        raise Exception(f"Error banning client: {e}")

async def _server_info(args: dict = None) -> list[TextContent]:
    """Get server information."""
    
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    try:
        response = await asyncio.to_thread(connection.connection.serverinfo)
        
        # Extract the first (and usually only) result
        if hasattr(response, 'parsed') and response.parsed:
            info = response.parsed[0]
        elif hasattr(response, '__getitem__'):
            # Use container emulation
            info = response[0]
        else:
            raise Exception("Unexpected response format")
        
        result = "🖥️ **TeamSpeak Server Information:**\n\n"
        result += f"• **Name**: {info.get('virtualserver_name', 'N/A')}\n"
        result += f"• **Version**: {info.get('virtualserver_version', 'N/A')}\n"
        result += f"• **Platform**: {info.get('virtualserver_platform', 'N/A')}\n"
        result += f"• **Clients**: {info.get('virtualserver_clientsonline', 'N/A')}/{info.get('virtualserver_maxclients', 'N/A')}\n"
        result += f"• **Uptime**: {info.get('virtualserver_uptime', 'N/A')} seconds\n"
        result += f"• **Port**: {info.get('virtualserver_port', 'N/A')}\n"
        result += f"• **Created**: {info.get('virtualserver_created', 'N/A')}\n"
        result += f"• **Auto Start**: {'Yes' if info.get('virtualserver_autostart') == '1' else 'No'}\n"
        result += f"• **Machine ID**: {info.get('virtualserver_machine_id', 'N/A')}\n"
        result += f"• **Unique ID**: {info.get('virtualserver_unique_identifier', 'N/A')}\n"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error retrieving server info: {e}")

async def _update_channel(args: dict) -> list[TextContent]:
    """Update channel properties."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    channel_id = args["channel_id"]
    
    # Build kwargs dict with only non-None values
    kwargs = {"cid": channel_id}
    
    if args.get("name"):
        kwargs["channel_name"] = args["name"]
    if args.get("description"):
        kwargs["channel_description"] = args["description"]  
    if args.get("password") is not None:
        kwargs["channel_password"] = args["password"]
    if args.get("max_clients"):
        kwargs["channel_maxclients"] = args["max_clients"]
    if args.get("talk_power") is not None:
        kwargs["channel_needed_talk_power"] = args["talk_power"]
    if args.get("codec_quality"):
        kwargs["channel_codec_quality"] = args["codec_quality"]
    if args.get("permanent") is not None:
        kwargs["channel_flag_permanent"] = 1 if args["permanent"] else 0
    
    try:
        await asyncio.to_thread(connection.connection.channeledit, **kwargs)
        
        changes = [k.replace("channel_", "") for k in kwargs.keys() if k != "cid"]
        result = f"✅ Channel {channel_id} updated successfully\n"
        result += f"📝 Modified properties: {', '.join(changes)}"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error updating channel: {e}")

async def _set_channel_talk_power(args: dict) -> list[TextContent]:
    """Set talk power requirement for a channel."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    channel_id = args["channel_id"]
    talk_power = args.get("talk_power")
    preset = args.get("preset")
    
    # Handle presets
    if preset:
        if preset == "silent":
            talk_power = 999
        elif preset == "moderated":
            talk_power = 50
        elif preset == "normal":
            talk_power = 0
    
    if talk_power is None:
        raise Exception("Either talk_power or preset must be specified")
    
    try:
        await asyncio.to_thread(
            connection.connection.channeledit,
            cid=channel_id,
            channel_needed_talk_power=talk_power
        )
        
        preset_text = f" (preset: {preset})" if preset else ""
        result = f"✅ Talk power for channel {channel_id} set to {talk_power}{preset_text}\n"
        
        if talk_power == 0:
            result += "🔊 Channel is now open - everyone can talk"
        elif talk_power >= 999:
            result += "🔇 Channel is now silent - only high-privilege users can talk"
        elif talk_power >= 50:
            result += "🔒 Channel is now moderated - only moderators+ can talk"
        else:
            result += f"⚡ Custom talk power requirement: {talk_power}"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error setting channel talk power: {e}")

async def _channel_info(args: dict) -> list[TextContent]:
    """Get detailed information about a specific channel."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    channel_id = args["channel_id"]
    
    try:
        response = await asyncio.to_thread(connection.connection.channelinfo, cid=channel_id)
        
        # Extract the first (and usually only) result
        if hasattr(response, 'parsed') and response.parsed:
            info = response.parsed[0]
        elif hasattr(response, '__getitem__'):
            # Use container emulation
            info = response[0]
        else:
            raise Exception("Unexpected response format")
        
        result = "📋 **Channel Information:**\n\n"
        result += f"• **ID**: {info.get('cid', 'N/A')}\n"
        result += f"• **Name**: {info.get('channel_name', 'N/A')}\n"
        result += f"• **Description**: {info.get('channel_description', 'N/A')}\n"
        result += f"• **Topic**: {info.get('channel_topic', 'N/A')}\n"
        result += f"• **Password Protected**: {'Yes' if info.get('channel_flag_password') == '1' else 'No'}\n"
        result += f"• **Max Clients**: {info.get('channel_maxclients', 'Unlimited')}\n"
        result += f"• **Current Clients**: {info.get('total_clients', '0')}\n"
        result += f"• **Talk Power Required**: {info.get('channel_needed_talk_power', '0')}\n"
        result += f"• **Codec**: {info.get('channel_codec', 'N/A')}\n"
        result += f"• **Codec Quality**: {info.get('channel_codec_quality', 'N/A')}\n"
        result += f"• **Type**: {'Permanent' if info.get('channel_flag_permanent') == '1' else 'Temporary'}\n"
        result += f"• **Order**: {info.get('channel_order', 'N/A')}\n"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error retrieving channel info: {e}")

async def _manage_channel_permissions(args: dict) -> list[TextContent]:
    """Add or remove specific permissions for a channel."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    channel_id = args["channel_id"]
    action = args["action"]
    permission = args.get("permission")
    value = args.get("value")
    
    try:
        if action == "add":
            if not permission or value is None:
                raise ValueError("Permission name and value required for add action")
            
            await asyncio.to_thread(
                connection.connection.channeladdperm,
                cid=channel_id, permsid=permission, permvalue=value
            )
            result = f"✅ Permission '{permission}' added to channel {channel_id} with value {value}"
            
        elif action == "remove":
            if not permission:
                raise ValueError("Permission name required for remove action")
            
            await asyncio.to_thread(
                connection.connection.channeldelperm,
                cid=channel_id, permsid=permission
            )
            result = f"✅ Permission '{permission}' removed from channel {channel_id}"
            
        elif action == "list":
            perms_response = await asyncio.to_thread(
                connection.connection.channelpermlist,
                cid=channel_id, permsid=True
            )
            
            if hasattr(perms_response, 'parsed'):
                perms = perms_response.parsed
            else:
                perms = list(perms_response)
            
            result = f"📋 **Channel {channel_id} Permissions:**\n\n"
            if perms:
                for perm in perms:
                    perm_name = perm.get('permsid', 'N/A')
                    perm_value = perm.get('permvalue', 'N/A')
                    result += f"• **{perm_name}**: {perm_value}\n"
            else:
                result += "No custom permissions set for this channel."
                
        else:
            raise ValueError(f"Unknown action: {action}")
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error managing channel permissions: {e}")

async def _client_info_detailed(args: dict) -> list[TextContent]:
    """Get detailed information about a specific client."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    client_id = args["client_id"]
    
    try:
        response = await asyncio.to_thread(connection.connection.clientinfo, clid=client_id)
        
        # Extract the first (and usually only) result
        if hasattr(response, 'parsed') and response.parsed:
            info = response.parsed[0]
        elif hasattr(response, '__getitem__'):
            # Use container emulation
            info = response[0]
        else:
            raise Exception("Unexpected response format")
        
        result = "👤 **Client Information:**\n\n"
        
        # Basic identification
        result += f"• **ID**: {info.get('clid', 'N/A')}\n"
        result += f"• **Database ID**: {info.get('client_database_id', 'N/A')}\n"
        result += f"• **Nickname**: {info.get('client_nickname', 'N/A')}\n"
        
        # Unique identifier (truncate if too long)
        unique_id = info.get('client_unique_identifier', 'N/A')
        if unique_id != 'N/A' and len(str(unique_id)) > 32:
            unique_id = str(unique_id)[:32] + "..."
        result += f"• **Unique ID**: {unique_id}\n"
        
        # Location and channel
        result += f"• **Channel ID**: {info.get('cid', 'N/A')}\n"
        
        # Client capabilities and status
        result += f"• **Talk Power**: {info.get('client_talk_power', '0')}\n"
        result += f"• **Client Type**: {'ServerQuery' if info.get('client_type') == '1' else 'Regular'}\n"
        result += f"• **Platform**: {info.get('client_platform', 'N/A')}\n"
        result += f"• **Version**: {info.get('client_version', 'N/A')}\n"
        
        # Status information
        result += f"• **Away**: {'Yes' if info.get('client_away') == '1' else 'No'}\n"
        result += f"• **Away Message**: {info.get('client_away_message', 'N/A')}\n"
        
        # Audio status
        result += f"• **Input Muted**: {'Yes' if info.get('client_input_muted') == '1' else 'No'}\n"
        result += f"• **Output Muted**: {'Yes' if info.get('client_output_muted') == '1' else 'No'}\n"
        result += f"• **Input Hardware**: {'Yes' if info.get('client_input_hardware') == '1' else 'No'}\n"
        result += f"• **Output Hardware**: {'Yes' if info.get('client_output_hardware') == '1' else 'No'}\n"
        
        # Timing information
        result += f"• **Created**: {info.get('client_created', 'N/A')}\n"
        result += f"• **Last Connected**: {info.get('client_lastconnected', 'N/A')}\n"
        result += f"• **Connection Time**: {info.get('connection_connected_time', 'N/A')}ms\n"
        
        # Geographic information
        result += f"• **Country**: {info.get('client_country', 'N/A')}\n"
        result += f"• **IP Address**: {info.get('connection_client_ip', 'N/A')}\n"
        result += f"• **Idle Time**: {info.get('client_idle_time', 'N/A')}ms\n"
        result += f"• **Is Recording**: {'Yes' if info.get('client_is_recording') == '1' else 'No'}\n"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error retrieving client info: {e}")

async def _update_server_settings(args: dict) -> list[TextContent]:
    """Update virtual server settings."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    name = args.get("name")
    welcome_message = args.get("welcome_message")
    max_clients = args.get("max_clients")
    password = args.get("password")
    hostmessage = args.get("hostmessage")
    hostmessage_mode = args.get("hostmessage_mode")
    default_server_group = args.get("default_server_group")
    default_channel_group = args.get("default_channel_group")
    
    try:
        kwargs = {}
        if name:
            kwargs["virtualserver_name"] = name
        if welcome_message:
            kwargs["virtualserver_welcomemessage"] = welcome_message
        if max_clients:
            kwargs["virtualserver_maxclients"] = max_clients
        if password:
            kwargs["virtualserver_password"] = password
        if hostmessage:
            kwargs["virtualserver_hostmessage"] = hostmessage
            kwargs["virtualserver_hostmessage_mode"] = hostmessage_mode
        if default_server_group:
            kwargs["virtualserver_default_server_group"] = default_server_group
        if default_channel_group:
            kwargs["virtualserver_default_channel_group"] = default_channel_group
        
        await asyncio.to_thread(connection.connection.serveredit, **kwargs)
        
        changes = [k for k, v in kwargs.items() if v is not None]
        result = f"✅ Server settings updated successfully\n"
        result += f"📝 Modified properties: {', '.join(changes)}"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error updating server settings: {e}")

async def _manage_user_permissions(args: dict) -> list[TextContent]:
    """Manage user permissions."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    client_id = args["client_id"]
    action = args["action"]
    group_id = args.get("group_id")
    permission = args.get("permission")
    value = args.get("value")
    skip = args.get("skip", False)
    negate = args.get("negate", False)
    
    try:
        # First, get client database ID for some operations
        client_info = None
        if action in ["list_groups", "add_permission", "remove_permission", "list_permissions"]:
            client_info_response = await asyncio.to_thread(connection.connection.clientinfo, clid=client_id)
            
            if hasattr(client_info_response, 'parsed') and client_info_response.parsed:
                client_info = client_info_response.parsed[0]
            elif hasattr(client_info_response, '__getitem__'):
                client_info = client_info_response[0]
            else:
                raise Exception("Could not get client info")
        
        if action == "add_group":
            if not group_id:
                raise ValueError("Server group ID required for add_group action")
            
            # Get client database ID first
            client_info_response = await asyncio.to_thread(connection.connection.clientinfo, clid=client_id)
            
            if hasattr(client_info_response, 'parsed') and client_info_response.parsed:
                client_info = client_info_response.parsed[0]
            elif hasattr(client_info_response, '__getitem__'):
                client_info = client_info_response[0]
            else:
                raise Exception("Could not get client info")
            
            client_database_id = client_info.get('client_database_id')
            if not client_database_id:
                raise ValueError("Could not get client database ID")
            
            await asyncio.to_thread(
                connection.connection.servergroupaddclient,
                sgid=group_id, cldbid=client_database_id
            )
            result = f"✅ Client {client_id} added to server group {group_id}"
            
        elif action == "remove_group":
            if not group_id:
                raise ValueError("Server group ID required for remove_group action")
            
            # Get client database ID first
            client_info_response = await asyncio.to_thread(connection.connection.clientinfo, clid=client_id)
            
            if hasattr(client_info_response, 'parsed') and client_info_response.parsed:
                client_info = client_info_response.parsed[0]
            elif hasattr(client_info_response, '__getitem__'):
                client_info = client_info_response[0]
            else:
                raise Exception("Could not get client info")
            
            client_database_id = client_info.get('client_database_id')
            if not client_database_id:
                raise ValueError("Could not get client database ID")
            
            await asyncio.to_thread(
                connection.connection.servergroupdelclient,
                sgid=group_id, cldbid=client_database_id
            )
            result = f"✅ Client {client_id} removed from server group {group_id}"
            
        elif action == "list_groups":
            # Use the client database ID to get server groups
            client_database_id = client_info.get('client_database_id')
            if not client_database_id:
                raise ValueError("Could not get client database ID")
            
            groups_response = await asyncio.to_thread(
                connection.connection.servergroupsbyclientid,
                cldbid=client_database_id
            )
            
            if hasattr(groups_response, 'parsed'):
                groups = groups_response.parsed
            else:
                groups = list(groups_response)
            
            result = f"📋 **Client {client_id} Server Groups:**\n\n"
            if groups:
                for group in groups:
                    group_name = group.get('name', 'N/A')
                    group_id = group.get('sgid', 'N/A')
                    result += f"• **{group_name}** (ID: {group_id})\n"
            else:
                result += "No server groups assigned to this client."
                
        elif action == "add_permission":
            if not permission or value is None:
                raise ValueError("Permission name and value required for add_permission action")
            
            client_database_id = client_info.get('client_database_id')
            if not client_database_id:
                raise ValueError("Could not get client database ID")
            
            await asyncio.to_thread(
                connection.connection.clientaddperm,
                cldbid=client_database_id, permsid=permission, permvalue=value, permskip=skip
            )
            result = f"✅ Permission '{permission}' added to client {client_id} with value {value}"
            
        elif action == "remove_permission":
            if not permission:
                raise ValueError("Permission name required for remove_permission action")
            
            client_database_id = client_info.get('client_database_id')
            if not client_database_id:
                raise ValueError("Could not get client database ID")
            
            await asyncio.to_thread(
                connection.connection.clientdelperm,
                cldbid=client_database_id, permsid=permission
            )
            result = f"✅ Permission '{permission}' removed from client {client_id}"
            
        elif action == "list_permissions":
            client_database_id = client_info.get('client_database_id')
            if not client_database_id:
                raise ValueError("Could not get client database ID")
            
            perms_response = await asyncio.to_thread(
                connection.connection.clientpermlist,
                cldbid=client_database_id, permsid=True
            )
            
            if hasattr(perms_response, 'parsed'):
                perms = perms_response.parsed
            else:
                perms = list(perms_response)
            
            result = f"📋 **Client {client_id} Permissions:**\n\n"
            if perms:
                for perm in perms:
                    perm_name = perm.get('permsid', 'N/A')
                    perm_value = perm.get('permvalue', 'N/A')
                    result += f"• **{perm_name}**: {perm_value}\n"
            else:
                result += "No custom permissions assigned to this client."
                
        else:
            raise ValueError(f"Unknown action: {action}")
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error managing user permissions: {e}")

async def _diagnose_permissions(args: dict = None) -> list[TextContent]:
    """Diagnose current connection permissions and provide troubleshooting help."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    result = "🔍 **Diagnostic des Permissions TeamSpeak MCP**\n\n"
    
    # Test 1: Basic whoami
    try:
        whoami_response = await asyncio.to_thread(connection.connection.whoami)
        
        if hasattr(whoami_response, 'parsed') and whoami_response.parsed:
            whoami = whoami_response.parsed[0]
        elif hasattr(whoami_response, '__getitem__'):
            whoami = whoami_response[0]
        else:
            raise Exception("Could not parse whoami response")
            
        result += "✅ **Connexion de base** : OK\n"
        result += f"   - Client ID: {whoami.get('client_id', 'N/A')}\n"
        result += f"   - Database ID: {whoami.get('client_database_id', 'N/A')}\n"
        result += f"   - Nickname: {whoami.get('client_nickname', 'N/A')}\n"
        result += f"   - Type: {'ServerQuery' if whoami.get('client_type') == '1' else 'Regular'}\n\n"
        
        # Store client_database_id for later use
        client_db_id = whoami.get('client_database_id')
        
    except Exception as e:
        result += f"❌ **Connexion de base** : ÉCHEC\n   Erreur: {e}\n\n"
        return [TextContent(type="text", text=result)]
    
    # Test 2: Server info (basic permission)
    try:
        await asyncio.to_thread(connection.connection.serverinfo)
        result += "✅ **server_info** : OK (permissions de base)\n"
    except Exception as e:
        result += f"❌ **server_info** : ÉCHEC - {e}\n"
    
    # Test 3: Client list (elevated permission)
    try:
        await asyncio.to_thread(connection.connection.clientlist)
        result += "✅ **list_clients** : OK (permissions élevées)\n"
    except Exception as e:
        result += f"❌ **list_clients** : ÉCHEC - {e}\n"
    
    # Test 4: Channel list
    try:
        await asyncio.to_thread(connection.connection.channellist)
        result += "✅ **list_channels** : OK\n"
    except Exception as e:
        result += f"❌ **list_channels** : ÉCHEC - {e}\n"
    
    # Test 5: Try to get current permissions
    try:
        if client_db_id and client_db_id != 'N/A':
            # Try to get server groups
            try:
                groups_response = await asyncio.to_thread(connection.connection.servergroupsbyclientid, cldbid=client_db_id)
                
                if hasattr(groups_response, 'parsed'):
                    groups = groups_response.parsed
                else:
                    groups = list(groups_response)
                
                result += f"✅ **Groupes serveur** : OK\n"
                for group in groups[:3]:  # Limit to first 3 groups
                    group_name = group.get('name', 'N/A')
                    group_id = group.get('sgid', 'N/A')
                    result += f"   - {group_name} (ID: {group_id})\n"
                    
            except Exception as e:
                result += f"❌ **Groupes serveur** : ÉCHEC - {e}\n"
        else:
            result += f"⚠️ **Groupes serveur** : Impossible (pas de client_database_id)\n"
            
    except Exception as e:
        result += f"❌ **Analyse des permissions** : ÉCHEC - {e}\n"
    
    result += "\n**📊 Configuration actuelle :**\n"
    result += f"   - Host: {connection.host}:{connection.port}\n"
    result += f"   - User: {connection.user}\n"
    result += f"   - Password: {'✅ Fourni' if connection.password else '❌ Non fourni'}\n"
    result += f"   - Server ID: {connection.server_id}\n\n"
    
    result += "**💡 Recommandations :**\n\n"
    result += "Si vous avez des échecs :\n"
    result += "1. **Vérifiez votre mot de passe ServerQuery**\n"
    result += "2. **Utilisez un token admin** si disponible\n"
    result += "3. **Créez un utilisateur ServerQuery avec permissions admin**\n"
    result += "4. **Vérifiez que le port 10011 (ServerQuery) est accessible**\n\n"
    result += "Pour plus d'aide, utilisez la commande `list_clients` qui fournit un diagnostic détaillé en cas d'erreur."
    
    return [TextContent(type="text", text=result)]

async def _list_server_groups(args: dict = None) -> list[TextContent]:
    """List all server groups available on the virtual server."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    try:
        response = await asyncio.to_thread(connection.connection.servergrouplist)
        
        # Extract groups list - response.parsed is a list of dictionaries
        if hasattr(response, 'parsed'):
            groups = response.parsed
        else:
            # Fallback to container emulation
            groups = list(response)
        
        result = "👥 **Server Groups:**\n\n"
        for group in groups:
            group_id = group.get('sgid', 'N/A')
            group_name = group.get('name', 'N/A')
            group_type = group.get('type', 'N/A')
            result += f"• **ID {group_id}**: {group_name} (Type: {group_type})\n"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error retrieving server groups: {e}")

async def _assign_client_to_group(args: dict) -> list[TextContent]:
    """Add or remove a client from a server group."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    client_database_id = args["client_database_id"]
    action = args["action"]
    group_id = args["group_id"]
    
    try:
        if action == "add":
            await asyncio.to_thread(
                connection.connection.servergroupaddclient,
                sgid=group_id, cldbid=client_database_id
            )
            result = f"✅ Client {client_database_id} added to server group {group_id}"
        elif action == "remove":
            await asyncio.to_thread(
                connection.connection.servergroupdelclient,
                sgid=group_id, cldbid=client_database_id
            )
            result = f"✅ Client {client_database_id} removed from server group {group_id}"
        else:
            raise ValueError(f"Unknown action: {action}")
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error managing client group membership: {e}")

async def _create_server_group(args: dict) -> list[TextContent]:
    """Create a new server group with specified name and type."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    name = args["name"]
    group_type = args.get("type", 1)
    
    try:
        response = await asyncio.to_thread(
            connection.connection.servergroupadd,
            name=name, type_=group_type
        )
        
        # Try to extract the new group ID from response
        result = f"✅ Server group '{name}' created successfully"
        if hasattr(response, 'parsed') and response.parsed:
            group_info = response.parsed[0]
            if 'sgid' in group_info:
                result += f" (ID: {group_info['sgid']})"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error creating server group: {e}")

async def _manage_server_group_permissions(args: dict) -> list[TextContent]:
    """Add, remove or list permissions for a server group."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    group_id = args["group_id"]
    action = args["action"]
    permission = args.get("permission")
    value = args.get("value")
    skip = args.get("skip", False)
    negate = args.get("negate", False)
    
    try:
        if action == "add":
            if not permission or value is None:
                raise ValueError("Permission name and value required for add action")
            
            await asyncio.to_thread(
                connection.connection.servergroupaddperm,
                sgid=group_id, permsid=permission, permvalue=value
            )
            result = f"✅ Permission '{permission}' added to server group {group_id} with value {value}"
        elif action == "remove":
            if not permission:
                raise ValueError("Permission name required for remove action")
            
            await asyncio.to_thread(
                connection.connection.servergroupdelperm,
                sgid=group_id, permsid=permission
            )
            result = f"✅ Permission '{permission}' removed from server group {group_id}"
        elif action == "list":
            perms_response = await asyncio.to_thread(
                connection.connection.servergrouppermlist,
                sgid=group_id, permsid=True
            )
            
            if hasattr(perms_response, 'parsed'):
                perms = perms_response.parsed
            else:
                perms = list(perms_response)
            
            result = f"📋 **Server Group {group_id} Permissions:**\n\n"
            if perms:
                for perm in perms:
                    perm_name = perm.get('permsid', 'N/A')
                    perm_value = perm.get('permvalue', 'N/A')
                    result += f"• **{perm_name}**: {perm_value}\n"
            else:
                result += "No custom permissions set for this server group."
        else:
            raise ValueError(f"Unknown action: {action}")
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error managing server group permissions: {e}")

async def _list_bans(args: dict = None) -> list[TextContent]:
    """List all active ban rules on the virtual server."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    try:
        response = await asyncio.to_thread(connection.connection.banlist)
        
        # Extract bans list - response.parsed is a list of dictionaries
        if hasattr(response, 'parsed'):
            bans = response.parsed
        else:
            # Fallback to container emulation
            bans = list(response)
        
        result = "📋 **Active Ban Rules:**\n\n"
        for ban in bans:
            ban_id = ban.get('banid', 'N/A')
            ip = ban.get('ip', 'N/A')
            name = ban.get('name', 'N/A')
            uid = ban.get('uid', 'N/A')
            time = ban.get('time', 'N/A')
            reason = ban.get('reason', 'N/A')
            result += f"• **ID**: {ban_id}\n"
            result += f"   - IP: {ip}\n"
            result += f"   - Name: {name}\n"
            result += f"   - UID: {uid}\n"
            result += f"   - Duration: {time} seconds\n"
            result += f"   - Reason: {reason}\n\n"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error retrieving ban rules: {e}")

async def _manage_ban_rules(args: dict) -> list[TextContent]:
    """Create, delete or manage ban rules."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    action = args["action"]
    ban_id = args.get("ban_id")
    ip = args.get("ip")
    name = args.get("name")
    uid = args.get("uid")
    time = args.get("time", 0)
    reason = args.get("reason", "Banned by AI")
    
    try:
        if action == "add":
            await asyncio.to_thread(
                connection.connection.banadd,
                ip=ip, name=name, uid=uid, time=time, reason=reason
            )
            result = f"✅ Ban rule added successfully"
        elif action == "delete":
            if not ban_id:
                raise ValueError("Ban ID required for delete action")
            
            await asyncio.to_thread(
                connection.connection.bandel,
                banid=ban_id
            )
            result = f"✅ Ban rule {ban_id} deleted successfully"
        elif action == "delete_all":
            await asyncio.to_thread(
                connection.connection.bandelall
            )
            result = "✅ All ban rules deleted successfully"
        else:
            raise ValueError(f"Unknown action: {action}")
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error managing ban rules: {e}")

async def _list_complaints(args: dict) -> list[TextContent]:
    """List complaints on the virtual server."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    target_client_database_id = args.get("target_client_database_id")
    
    try:
        response = await asyncio.to_thread(connection.connection.complaintlist)
        
        # Extract complaints list - response.parsed is a list of dictionaries
        if hasattr(response, 'parsed'):
            complaints = response.parsed
        else:
            # Fallback to container emulation
            complaints = list(response)
        
        result = "📋 **Complaints:**\n\n"
        for complaint in complaints:
            complaint_id = complaint.get('complaintid', 'N/A')
            client_database_id = complaint.get('cldbid', 'N/A')
            reason = complaint.get('reason', 'N/A')
            result += f"• **ID**: {complaint_id}\n"
            result += f"   - Client ID: {client_database_id}\n"
            result += f"   - Reason: {reason}\n\n"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error retrieving complaints: {e}")

async def _search_clients(args: dict) -> list[TextContent]:
    """Search for clients by name pattern or unique identifier."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    pattern = args["pattern"]
    search_by_uid = args.get("search_by_uid", False)
    
    try:
        if search_by_uid:
            response = await asyncio.to_thread(
                connection.connection.clientdbfind,
                pattern=pattern, uid=True
            )
        else:
            response = await asyncio.to_thread(
                connection.connection.clientfind,
                pattern=pattern
            )
        
        # Extract clients list - response.parsed is a list of dictionaries
        if hasattr(response, 'parsed'):
            clients = response.parsed
        else:
            # Fallback to container emulation
            clients = list(response)
        
        result = f"👥 **Search Results for '{pattern}':**\n\n"
        if not clients:
            result += "No clients found matching the pattern."
        else:
            for client in clients:
                if search_by_uid:
                    client_id = client.get('cldbid', 'N/A')
                    nickname = client.get('client_nickname', 'N/A')
                    result += f"• **DB ID {client_id}**: {nickname}\n"
                else:
                    client_id = client.get('clid', 'N/A')
                    nickname = client.get('client_nickname', 'N/A')
                    result += f"• **ID {client_id}**: {nickname}\n"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error searching for clients: {e}")

async def _find_channels(args: dict) -> list[TextContent]:
    """Search for channels by name pattern."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    pattern = args["pattern"]
    
    try:
        response = await asyncio.to_thread(
            connection.connection.channelfind,
            pattern=pattern
        )
        
        # Extract channels list - response.parsed is a list of dictionaries
        if hasattr(response, 'parsed'):
            channels = response.parsed
        else:
            # Fallback to container emulation
            channels = list(response)
        
        result = f"📋 **Channel Search Results for '{pattern}':**\n\n"
        if not channels:
            result += "No channels found matching the pattern."
        else:
            for channel in channels:
                channel_id = channel.get('cid', 'N/A')
                channel_name = channel.get('channel_name', 'N/A')
                result += f"• **ID {channel_id}**: {channel_name}\n"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error searching for channels: {e}")

async def _list_privilege_tokens(args: dict = None) -> list[TextContent]:
    """List all privilege keys/tokens available on the server."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    try:
        response = await asyncio.to_thread(connection.connection.tokenlist)
        
        # Extract tokens list - response.parsed is a list of dictionaries
        if hasattr(response, 'parsed'):
            tokens = response.parsed
        else:
            # Fallback to container emulation
            tokens = list(response)
        
        result = "🔑 **Privilege Tokens:**\n\n"
        if not tokens:
            result += "No privilege tokens found."
        else:
            for token in tokens:
                token_key = token.get('token', 'N/A')[:20] + "..." if len(token.get('token', '')) > 20 else token.get('token', 'N/A')
                token_type = "Server Group" if token.get('token_type') == '0' else "Channel Group" if token.get('token_type') == '1' else 'Unknown'
                token_id1 = token.get('token_id1', 'N/A')
                token_description = token.get('token_description', 'No description')
                result += f"• **Token**: {token_key}\n"
                result += f"  - Type: {token_type} (ID: {token_id1})\n"
                result += f"  - Description: {token_description}\n\n"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error retrieving privilege tokens: {e}")

async def _create_privilege_token(args: dict) -> list[TextContent]:
    """Create a new privilege key/token for server or channel group access."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    token_type = args["token_type"]
    group_id = args["group_id"]
    channel_id = args.get("channel_id", 0)
    description = args.get("description", "")
    custom_set = args.get("custom_set", "")
    
    try:
        response = await asyncio.to_thread(
            connection.connection.tokenadd,
            tokentype=token_type,
            tokenid1=group_id,
            tokenid2=channel_id,
            tokendescription=description,
            tokencustomset=custom_set
        )
        
        # Extract the token from response
        if hasattr(response, 'parsed') and response.parsed:
            token_info = response.parsed[0]
            token = token_info.get('token', 'N/A')
            result = f"✅ Privilege token created successfully\n"
            result += f"🔑 **Token**: {token}"
        else:
            result = f"✅ Privilege token created successfully"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error creating privilege token: {e}")

async def _list_files(args: dict) -> list[TextContent]:
    """List files in a channel's file repository."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    channel_id = args["channel_id"]
    path = args.get("path", "/")
    channel_password = args.get("channel_password", "")
    
    try:
        response = await asyncio.to_thread(
            connection.connection.ftgetfilelist,
            cid=channel_id,
            path=path,
            cpw=channel_password
        )
        
        # Extract files list - response.parsed is a list of dictionaries
        if hasattr(response, 'parsed'):
            files = response.parsed
        else:
            # Fallback to container emulation
            files = list(response)
        
        result = f"📁 **Files in Channel {channel_id} (Path: {path}):**\n\n"
        if not files:
            result += "No files found in this directory."
        else:
            for file in files:
                file_name = file.get('name', 'N/A')
                file_size = file.get('size', 'N/A')
                file_type = "Directory" if file.get('type') == '0' else "File"
                result += f"• **{file_name}** ({file_type})\n"
                if file_type == "File":
                    result += f"  - Size: {file_size} bytes\n"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error retrieving files: {e}")

async def _get_file_info(args: dict) -> list[TextContent]:
    """Get detailed information about a specific file in a channel."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    channel_id = args["channel_id"]
    file_path = args["file_path"]
    channel_password = args.get("channel_password", "")
    
    try:
        response = await asyncio.to_thread(
            connection.connection.ftgetfileinfo,
            cid=channel_id,
            name=file_path,
            cpw=channel_password
        )
        
        # Extract file info - response.parsed is a list of dictionaries
        if hasattr(response, 'parsed') and response.parsed:
            info = response.parsed[0]
        else:
            # Fallback to container emulation
            info = response[0] if response else {}
        
        result = f"📄 **File Information for '{file_path}':**\n\n"
        for key, value in info.items():
            # Format key for better readability
            display_key = key.replace('_', ' ').title()
            result += f"• **{display_key}**: {value}\n"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error retrieving file info: {e}")

async def _manage_file_permissions(args: dict) -> list[TextContent]:
    """List active file transfers and manage file transfer permissions."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    action = args["action"]
    transfer_id = args.get("transfer_id")
    delete_partial = args.get("delete_partial", False)
    
    try:
        if action == "list_transfers":
            response = await asyncio.to_thread(connection.connection.ftlist)
            
            # Extract transfers list - response.parsed is a list of dictionaries
            if hasattr(response, 'parsed'):
                transfers = response.parsed
            else:
                # Fallback to container emulation
                transfers = list(response)
            
            result = "📋 **Active File Transfers:**\n\n"
            if not transfers:
                result += "No active file transfers."
            else:
                for transfer in transfers:
                    transfer_id = transfer.get('serverftfid', 'N/A')
                    client_id = transfer.get('clid', 'N/A')
                    file_name = transfer.get('name', 'N/A')
                    file_size = transfer.get('size', 'N/A')
                    status = transfer.get('status', 'N/A')
                    result += f"• **Transfer ID {transfer_id}**:\n"
                    result += f"  - Client: {client_id}\n"
                    result += f"  - File: {file_name}\n"
                    result += f"  - Size: {file_size} bytes\n"
                    result += f"  - Status: {status}\n\n"
        elif action == "stop_transfer":
            if not transfer_id:
                raise ValueError("Transfer ID required for stop_transfer action")
            
            await asyncio.to_thread(
                connection.connection.ftstop,
                serverftfid=transfer_id,
                delete=1 if delete_partial else 0
            )
            result = f"✅ File transfer {transfer_id} stopped"
        else:
            raise ValueError(f"Unknown action: {action}")
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error managing file permissions: {e}")

async def _view_server_logs(args: dict) -> list[TextContent]:
    """View recent entries from the virtual server log with enhanced options."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    lines = args.get("lines", 50)
    reverse = args.get("reverse", True)
    instance_log = args.get("instance_log", False)
    begin_pos = args.get("begin_pos")
    log_level = args.get("log_level")
    timestamp_from = args.get("timestamp_from")
    timestamp_to = args.get("timestamp_to")
    complete_mode = args.get("complete_mode", False)
    max_iterations = args.get("max_iterations", 1000)
    enhanced_debug = args.get("enhanced_debug", False)

    try:
        if complete_mode:
            # Mode complet avec pagination automatique
            return await _view_server_logs_complete_impl(
                lines, reverse, instance_log, max_iterations, enhanced_debug
            )
        elif enhanced_debug:
            # Mode debug amélioré
            return await _view_server_logs_enhanced_impl(
                lines, reverse, instance_log, begin_pos, enhanced_debug
            )
        else:
            # Mode standard amélioré
            kwargs = {}
            if lines:
                kwargs['lines'] = lines
            if reverse is not None:
                kwargs['reverse'] = 1 if reverse else 0
            if instance_log:
                kwargs['instance'] = 1
            if begin_pos:
                kwargs['begin_pos'] = begin_pos
            
            # Try enhanced parameters (may not be supported on all TS versions)
            if log_level:
                kwargs['loglevel'] = log_level
            if timestamp_from:
                kwargs['timestamp_begin'] = timestamp_from
            if timestamp_to:
                kwargs['timestamp_end'] = timestamp_to
                
            logger.info(f"Executing logview with parameters: {kwargs}")
            response = await asyncio.to_thread(connection.connection.logview, **kwargs)
            
            # Enhanced log data extraction
            if hasattr(response, 'parsed') and response.parsed:
                log_data = response.parsed[0] if response.parsed else {}
            else:
                log_data = response[0] if response else {}
            
            result = "📋 **Server Logs Enhanced:**\n\n"
            result += f"**Paramètres utilisés:** lines={lines}, reverse={reverse}, instance_log={instance_log}\n"
            if log_level:
                result += f"**Niveau de log:** {log_level}\n"
            result += "\n"
            
            # Multiple ways to extract log entries
            log_entries = []
            
            # Method 1: Standard 'l' field
            if 'l' in log_data:
                entries = log_data['l'].split('\\n')
                log_entries.extend([entry.strip() for entry in entries if entry.strip()])
            
            # Method 2: Check for alternative fields
            for field in ['log', 'logentry', 'entries', 'data']:
                if field in log_data:
                    if isinstance(log_data[field], str):
                        entries = log_data[field].split('\\n')
                        log_entries.extend([entry.strip() for entry in entries if entry.strip()])
                    elif isinstance(log_data[field], list):
                        log_entries.extend(log_data[field])
            
            # Method 3: If log_data is a list itself
            if isinstance(log_data, list):
                for item in log_data:
                    if isinstance(item, str):
                        log_entries.append(item.strip())
                    elif isinstance(item, dict) and 'l' in item:
                        entries = item['l'].split('\\n')
                        log_entries.extend([entry.strip() for entry in entries if entry.strip()])
            
            # Method 4: Raw response processing if nothing else works
            if not log_entries:
                raw_response = str(response)
                if '|' in raw_response:  # TeamSpeak log format has | separators
                    potential_logs = raw_response.split('\n')
                    for line in potential_logs:
                        if '|' in line and any(level in line for level in ['INFO', 'ERROR', 'WARNING', 'DEBUG']):
                            log_entries.append(line.strip())
            
            if log_entries:
                result += f"**{len(log_entries)} entrées trouvées:**\n\n"
                for i, entry in enumerate(log_entries[-lines:], 1):  # Take last N lines
                    if entry:
                        result += f"**{i}.** {entry}\n"
            else:
                result += "❌ **Aucune entrée de log trouvée.**\n\n"
                result += "**Données brutes reçues:**\n"
                result += f"```\n{str(log_data)[:500]}...\n```\n"
                result += "\n**Suggestion:** Vérifiez la configuration des logs du serveur TeamSpeak."
            
            # Additional debugging info
            result += f"\n**Debug info:**\n"
            result += f"- Type de response: {type(response)}\n"
            result += f"- Keys disponibles: {list(log_data.keys()) if isinstance(log_data, dict) else 'Non dict'}\n"
            result += f"- Taille des données: {len(str(log_data))} caractères\n"
            
            return [TextContent(type="text", text=result)]
            
    except Exception as e:
        raise Exception(f"Error retrieving server logs: {e}")

async def _view_server_logs_complete_impl(lines: int, reverse: bool, instance_log: bool, 
                                        max_iterations: int, enhanced_debug: bool) -> list[TextContent]:
    """
    Récupère TOUS les logs du serveur en paginant automatiquement
    Basé sur la recherche : il faut utiliser begin_pos avec last_pos pour tout récupérer
    """
    import time
    
    all_logs = []
    current_pos = None
    iteration = 0
    
    try:
        while iteration < max_iterations:
            # Paramètres pour la requête logview
            params = {
                'lines': min(lines, 100),  # Maximum 100 lignes par requête
                'reverse': 1 if reverse else 0,
                'instance': 1 if instance_log else 0
            }
            
            # Ajouter begin_pos seulement si on l'a (après la première requête)
            if current_pos is not None:
                params['begin_pos'] = current_pos
                # Après la première requête, récupérer seulement 1 ligne à la fois
                # pour éviter les lignes incomplètes
                params['lines'] = 1
            
            # Exécuter la requête logview
            response = await asyncio.to_thread(connection.connection.logview, **params)
            
            # Vérifier si on a des données
            if not hasattr(response, 'parsed') or not response.parsed:
                break
                
            # Extraire les logs de cette requête
            logs_batch = []
            for entry in response.parsed:
                if 'l' in entry:  # 'l' contient le texte du log
                    logs_batch.append(entry['l'])
            
            # Si pas de nouveaux logs, on a fini
            if not logs_batch:
                break
                
            # Ajouter à notre collection
            all_logs.extend(logs_batch)
            
            # Récupérer last_pos pour la prochaine iteration
            if hasattr(response, 'last_pos'):
                new_pos = getattr(response, 'last_pos', None)
                if new_pos == 0 or new_pos == current_pos:
                    # last_pos = 0 signifie qu'on a atteint la fin
                    break
                current_pos = new_pos
            else:
                # Pas de last_pos, on s'arrête
                break
                
            iteration += 1
            
            # Petit délai pour éviter de spammer le serveur
            await asyncio.sleep(0.1)
    
    except Exception as e:
        # Log l'erreur mais retourne ce qu'on a déjà récupéré
        logger.error(f"Erreur lors de la récupération des logs: {e}")
    
    # Formater la sortie
    if not all_logs:
        result = "Aucun log trouvé"
    else:
        # Trier les logs si nécessaire (par timestamp)
        formatted_logs = []
        for i, log_line in enumerate(all_logs, 1):
            formatted_logs.append(f"**{i}.** {log_line}")
    
        result = f"""📋 **Server Logs Complete (Enhanced):**

**Paramètres utilisés:** lines={lines}, reverse={reverse}, instance_log={instance_log}

**{len(all_logs)} entrées trouvées:**

{chr(10).join(formatted_logs)}

**Stats de récupération:**
- Itérations: {iteration}
- Position finale: {current_pos}
- Total des logs: {len(all_logs)}
"""

    return [TextContent(type="text", text=result)]

async def _view_server_logs_enhanced_impl(lines: int, reverse: bool, instance_log: bool, 
                                        begin_pos: int, enhanced_debug: bool) -> list[TextContent]:
    """
    Version améliorée qui gère mieux les différents cas d'erreur
    """
    try:
        # Configuration de base
        params = {
            'lines': min(lines, 100),  # TeamSpeak limite à 100
            'reverse': 1 if reverse else 0,
            'instance': 1 if instance_log else 0
        }
        
        if begin_pos is not None:
            params['begin_pos'] = begin_pos
        
        # Exécuter la requête
        response = await asyncio.to_thread(connection.connection.logview, **params)
        
        # Debug info
        debug_info = {
            'response_type': str(type(response)),
            'has_parsed': hasattr(response, 'parsed'),
            'has_last_pos': hasattr(response, 'last_pos'),
            'has_file_size': hasattr(response, 'file_size')
        }
        
        # Extraire les logs
        logs = []
        if hasattr(response, 'parsed') and response.parsed:
            for entry in response.parsed:
                if isinstance(entry, dict) and 'l' in entry:
                    logs.append(entry['l'])
                elif isinstance(entry, str):
                    logs.append(entry)
        
        # Informations de pagination
        last_pos = getattr(response, 'last_pos', None)
        file_size = getattr(response, 'file_size', None)
        
        # Formatage du résultat
        result = f"""📋 **Server Logs Enhanced:**

**Paramètres utilisés:** lines={lines}, reverse={reverse}, instance_log={instance_log}

**{len(logs)} entrées trouvées:**

"""
        
        for i, log_line in enumerate(logs, 1):
            result += f"**{i}.** {log_line}\n"
        
        result += f"""
**Debug info:**
- Type de response: {debug_info['response_type']}
- Has parsed: {debug_info['has_parsed']}
- Has last_pos: {debug_info['has_last_pos']} (value: {last_pos})
- Has file_size: {debug_info['has_file_size']} (value: {file_size})
- Taille des données: {len(str(response))} caractères

**Pagination info:**
- Position actuelle: {begin_pos}
- Prochaine position: {last_pos}
- Plus de données disponibles: {'Oui' if last_pos and last_pos > 0 else 'Non'}
"""
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        result = f"❌ **Erreur lors de la récupération des logs:**\n\nErreur: {str(e)}\nType: {type(e).__name__}"
        return [TextContent(type="text", text=result)]

async def _add_log_entry(args: dict) -> list[TextContent]:
    """Add a custom entry to the server log."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    log_level = args["log_level"]
    message = args["message"]
    
    try:
        await asyncio.to_thread(
            connection.connection.logadd,
            loglevel=log_level,
            message=message
        )
        result = f"✅ Log entry added successfully"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error adding log entry: {e}")

async def _get_connection_info(args: dict = None) -> list[TextContent]:
    """Get detailed connection information for the virtual server."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    try:
        response = await asyncio.to_thread(connection.connection.serverinfo)
        
        # Extract the first (and usually only) result
        if hasattr(response, 'parsed') and response.parsed:
            info = response.parsed[0]
        elif hasattr(response, '__getitem__'):
            # Use container emulation
            info = response[0]
        else:
            raise Exception("Unexpected response format")
        
        result = "🖥️ **Server Connection Information:**\n\n"
        for key, value in info.items():
            result += f"• **{key}**: {value}\n"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error retrieving connection info: {e}")

async def _create_server_snapshot(args: dict = None) -> list[TextContent]:
    """Create a snapshot of the virtual server configuration."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    try:
        response = await asyncio.to_thread(connection.connection.serversnapshotcreate)
        
        # Extract snapshot data
        if hasattr(response, 'parsed') and response.parsed:
            snapshot_data = response.parsed[0]
        else:
            snapshot_data = response[0] if response else {}
        
        result = "📸 **Server Snapshot Created Successfully**\n\n"
        result += "⚠️ **Important**: Save this snapshot data for restoration:\n\n"
        
        # The snapshot data is typically very long, so we'll show a preview
        if isinstance(snapshot_data, dict):
            for key, value in snapshot_data.items():
                if len(str(value)) > 100:
                    preview = str(value)[:100] + "..."
                    result += f"• **{key}**: {preview}\n"
                else:
                    result += f"• **{key}**: {value}\n"
        else:
            # If it's a string, show preview
            snapshot_str = str(snapshot_data)
            if len(snapshot_str) > 500:
                result += f"```\n{snapshot_str[:500]}...\n```\n"
            else:
                result += f"```\n{snapshot_str}\n```\n"
        
        result += "\n💡 **Tip**: Use `deploy_server_snapshot` to restore this configuration."
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error creating server snapshot: {e}")

async def _deploy_server_snapshot(args: dict) -> list[TextContent]:
    """Deploy/restore a server configuration from a snapshot."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    snapshot_data = args["snapshot_data"]
    
    try:
        await asyncio.to_thread(
            connection.connection.serversnapshotdeploy,
            virtualserver_snapshot=snapshot_data
        )
        result = "✅ Server snapshot deployed successfully\n\n"
        result += "⚠️ **Note**: The server configuration has been restored from the snapshot."
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error deploying server snapshot: {e}")

async def _get_instance_logs(args: dict) -> list[TextContent]:
    """Get instance-level logs instead of virtual server logs."""
    # Create connection with dynamic credentials if provided
    connection = get_connection_from_args(args)
    
    # Connect if not already connected
    if not connection.is_connected():
        success = await connection.connect()
        if not success:
            raise Exception("Failed to connect to TeamSpeak server")
    
    lines = args.get("lines", 50)
    reverse = args.get("reverse", True)
    begin_pos = args.get("begin_pos")
    
    try:
        kwargs = {
            "lines": lines,
            "reverse": 1 if reverse else 0,
            "instance": 1  # This requests instance logs instead of virtual server logs
        }
        
        if begin_pos is not None:
            kwargs["begin_pos"] = begin_pos
        
        response = await asyncio.to_thread(connection.connection.logview, **kwargs)
        
        result = f"📋 **TeamSpeak Instance Logs (last {lines} entries)**\n\n"
        
        if hasattr(response, 'parsed') and response.parsed:
            log_data = response.parsed[0]
            if 'l' in log_data:
                # Split log entries by newlines
                log_lines = log_data['l'].split('\\n')
                log_lines = [line.strip() for line in log_lines if line.strip()]
                
                if log_lines:
                    result += f"🔍 Found {len(log_lines)} log entries:\n\n"
                    for i, line in enumerate(log_lines, 1):
                        # Basic formatting to make logs more readable
                        if '|' in line:
                            parts = line.split('|', 3)
                            if len(parts) >= 3:
                                timestamp = parts[0].strip()
                                level = parts[1].strip()
                                message = '|'.join(parts[2:]).strip()
                                result += f"**{i}.** `{timestamp}` [{level}] {message}\n"
                            else:
                                result += f"**{i}.** {line}\n"
                        else:
                            result += f"**{i}.** {line}\n"
                else:
                    result += "ℹ️ No log entries found"
            else:
                result += "❌ No log data received from server"
        else:
            result += "❌ No response data received"
        
        result += f"\n\n💡 **Tip**: Use different parameters to filter results:\n"
        result += f"- `lines`: Number of entries (1-100)\n"
        result += f"- `reverse`: true for newest first, false for oldest first\n"
        result += f"- `begin_pos`: Starting position in log file"
        
        return [TextContent(type="text", text=result)]
    except Exception as e:
        raise Exception(f"Error retrieving instance logs: {e}")

def main():
    """Entry point for setuptools."""
    asyncio.run(run_server())

if __name__ == "__main__":
    main() 
