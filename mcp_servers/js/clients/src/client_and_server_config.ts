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
    {
        server_name :"ATLASSIAN",
        server_features_and_capability:`Atlassian Trello server provides comprehensive project management capabilities including board management, list operations, card management, team collaboration, and workflow automation. Supports creating/updating cards, managing lists, board operations, activity tracking, file attachments, and workspace management.`,
        path : "dist/index.js"
    },
    {
        server_name :"TABLEAU",
        server_features_and_capability:`Tableau MCP server provides comprehensive data visualization and analytics capabilities. Supports listing published data sources, executing VizQL queries, accessing metadata, and managing Tableau Server/Cloud resources. Enables AI assistants to interact with Tableau dashboards and data.`,
        path : "dist/index.js"
    },
]
