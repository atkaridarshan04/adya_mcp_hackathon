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
	}
]
