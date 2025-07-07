ClientsConfig =[
    "MCP_CLIENT_AZURE_AI",
    "MCP_CLIENT_OPENAI",
	"MCP_CLIENT_GEMINI"
]
ServersConfig = [
	# {
	# 	"server_name": "MCP-GSUITE",
	# 	"command":"uv",
	# 	"args": [
	# 		"--directory",
	# 		"../servers/MCP-GSUITE/mcp-gsuite",
	# 		"run",
	# 		"mcp-gsuite"
	# 	]
	# },
    {
		"server_name": "AWS-EC2",
		"server_features_and_capability": "AWS EC2 MCP server provides comprehensive AWS CLI integration with tools for executing AWS commands, getting help documentation, and managing AWS resources. Supports command pipelines with Unix utilities, AWS resource management, security auditing, cost optimization, and infrastructure automation following AWS Well-Architected Framework best practices.",
		"command": "uv",
		"args": [
			"--directory",
			"../servers/AWS-EC2",
			"run",
			"python",
			"-m",
			"aws_mcp_server"
		]
	},
	{
		"server_name": "TEAMSPEAK",
		"server_features_and_capability": "TeamSpeak MCP server provides comprehensive TeamSpeak server management capabilities including user management, channel operations, server administration, messaging, and real-time monitoring. Supports creating/deleting channels, managing user permissions, sending messages, kicking/banning users, and retrieving server statistics and client information.",
		"command": "python",
		"args": [
			"-m",
			"teamspeak_mcp.server"
		],
		"cwd": "../servers/TEAMSPEAK"
	},
    {
		"server_name": "WHATSAPP",
        "server_features_and_capability": "WhatsApp MCP server provides comprehensive WhatsApp Business API integration including messaging, group management, session handling, and chat history. Supports sending text messages, creating/managing groups, adding/removing participants, retrieving chat lists and message history, and managing WhatsApp API sessions through GreenAPI.",
		"command": "uv",
		"args": [
			"--directory",
			"../servers/WHATSAPP",
			"run",
			"whatsapp-mcp"
		]
	}
]
