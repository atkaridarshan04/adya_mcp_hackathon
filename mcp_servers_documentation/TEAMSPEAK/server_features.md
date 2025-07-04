# TeamSpeak MCP Server - Server Features

## Overview

A Model Context Protocol server that enables AI assistants to interact with TeamSpeak servers through the ServerQuery interface. This server provides comprehensive tools for managing TeamSpeak servers, channels, clients, permissions, and real-time monitoring.

## Available Tools

### Connection Management
- **connect_to_server**: Connect to the configured TeamSpeak server
- **server_info**: Get comprehensive TeamSpeak server information and statistics
- **get_connection_info**: Get detailed connection information for the virtual server

### Channel Operations
- **list_channels**: List all channels on the server with detailed information
- **create_channel**: Create a new channel with custom properties
- **delete_channel**: Delete an existing channel
- **update_channel**: Update channel properties (name, description, password, etc.)
- **channel_info**: Get detailed information about a specific channel
- **find_channels**: Search for channels by name pattern
- **set_channel_talk_power**: Set talk power requirement for channels

### Client Management
- **list_clients**: List all clients connected to the server
- **client_info_detailed**: Get detailed information about a specific client
- **search_clients**: Search for clients by name pattern or unique identifier
- **move_client**: Move a client to another channel
- **kick_client**: Kick a client from server or channel
- **ban_client**: Ban a client from the server

### Messaging System
- **send_channel_message**: Send a message to a TeamSpeak channel
- **send_private_message**: Send a private message to a user
- **poke_client**: Send a poke (alert notification) to a client

### Permission Management
- **manage_channel_permissions**: Add or remove specific permissions for channels
- **manage_user_permissions**: Manage user permissions and server group assignments
- **diagnose_permissions**: Diagnose current connection permissions and troubleshooting

### Server Group Operations
- **list_server_groups**: List all server groups available on the virtual server
- **assign_client_to_group**: Add or remove a client from a server group
- **create_server_group**: Create a new server group with specified name and type
- **manage_server_group_permissions**: Add, remove or list permissions for server groups

### Administration Tools
- **update_server_settings**: Update virtual server settings (name, welcome message, max clients)
- **list_bans**: List all active ban rules on the virtual server
- **manage_ban_rules**: Create, delete or manage ban rules
- **list_complaints**: List complaints on the virtual server

### File Management
- **list_files**: List files in a channel's file repository
- **get_file_info**: Get detailed information about a specific file in a channel
- **manage_file_permissions**: List active file transfers and manage file transfer permissions

### Logging & Monitoring
- **view_server_logs**: View recent entries from the virtual server log with enhanced options
- **add_log_entry**: Add a custom entry to the server log
- **get_instance_logs**: Get instance-level logs instead of virtual server logs

### Token Management
- **list_privilege_tokens**: List all privilege keys/tokens available on the server
- **create_privilege_token**: Create a new privilege key/token for server or channel group access

### Backup & Restore
- **create_server_snapshot**: Create a snapshot of the virtual server configuration
- **deploy_server_snapshot**: Deploy/restore a server configuration from a snapshot

## Key Features

### Real-time Server Management
- Live client and channel monitoring
- Dynamic permission management
- Real-time messaging and notifications
- Server statistics and performance monitoring

### User Administration
- Complete user lifecycle management
- Advanced permission system integration
- Group-based access control
- Client search and filtering capabilities

### Channel Management
- Hierarchical channel structure support
- Custom channel properties and permissions
- Talk power and access control
- Channel-specific file repositories

### Communication Tools
- Multi-channel messaging system
- Private messaging capabilities
- Alert notifications (pokes)
- Broadcast messaging support

## Prerequisites

- Python 3.8 or higher
- TeamSpeak Server with ServerQuery enabled
- Network access to TeamSpeak ServerQuery port (default: 10011)
- Valid ServerQuery credentials

## Authentication

- ServerQuery username and password
- Virtual server ID specification
- Host and port configuration
- Dynamic credential injection support

## Connection Requirements

- **Host**: TeamSpeak server IP address or hostname
- **Port**: ServerQuery port (typically 10011)
- **Username**: ServerQuery username (typically 'serveradmin')
- **Password**: ServerQuery password or privilege key
- **Server ID**: Virtual server ID (typically 1)

## Security Features

- Secure credential handling
- Dynamic connection management
- Permission-based access control
- Audit logging capabilities
