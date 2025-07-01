ClientsConfig = [
    "MCP_CLIENT_AZURE_AI",
    "MCP_CLIENT_OPENAI",
    "MCP_CLIENT_GEMINI"
]

ServersConfig = [
    {
        "server_name": "MCP-GSUITE",
        "command": "uv",
        "args": [
            "--directory",
            "../servers/MCP-GSUITE/mcp-gsuite",
            "run",
            "mcp-gsuite"
        ]
    },
    {
        "server_name": "Agora",
        "command": "uv",
        "args": [
            "--directory",
            "../servers/Agora",
            "run",
            "agora-mcp"
        ]
    }
]
