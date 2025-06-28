export const ClientsConfig:any = [
    "MCP_CLIENT_OPENAI",
    "MCP_CLIENT_AZURE_AI",
    "MCP_CLIENT_GEMINI",
    // "CLAUDE",
]

export const ServersConfig:any = [
    {
        server_name :"WORDPRESS",
        server_features_and_capability:`WORDPRESS`,
        path : "build/index.js"
    },
    {
        server_name :"GITHUB",
        server_features_and_capability:`GitHub server provides comprehensive repository management, file operations, issue tracking, pull request management, search functionality, and more. Supports creating/updating files, managing branches, creating issues/PRs, searching code/users/repositories, and handling Git operations.`,
        path : "dist/index.js"
    },
]
