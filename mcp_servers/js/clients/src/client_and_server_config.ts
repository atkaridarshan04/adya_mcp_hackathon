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
        server_name :"G_NEWS",
        server_features_and_capability:`Google News server provides access to news articles and content from around the world. Search for news by keywords, filter by country and language, and get categorized results by topics like AI & Technology, Business, Science & Research, and Healthcare.`,
        path : "dist/index.js"
    },
]
