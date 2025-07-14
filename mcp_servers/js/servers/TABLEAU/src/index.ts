#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from 'zod';

// Tableau API client
class TableauClient {
  private baseUrl: string;
  private siteName: string;
  private token: string;
  private siteId: string = '';

  constructor(server: string, siteName: string, patName: string, patValue: string) {
    this.baseUrl = server;
    this.siteName = siteName;
    this.token = Buffer.from(`${patName}:${patValue}`).toString('base64');
  }

  private async makeRequest(endpoint: string, method: string = 'GET', body?: any) {
    const url = `${this.baseUrl}/api/3.21${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'X-Tableau-Auth': this.token
    };

    const response = await fetch(url, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined
    });

    if (!response.ok) {
      throw new Error(`Tableau API error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  async signIn() {
    const response = await this.makeRequest('/auth/signin', 'POST', {
      credentials: {
        personalAccessTokenName: this.token.split(':')[0],
        personalAccessTokenSecret: this.token.split(':')[1],
        site: { contentUrl: this.siteName }
      }
    }) as any;
    this.siteId = response.credentials.site.id;
    this.token = response.credentials.token;
  }

  async listDatasources() {
    return this.makeRequest(`/sites/${this.siteId}/datasources`);
  }

  async queryDatasource(datasourceId: string, query: string) {
    return this.makeRequest(`/sites/${this.siteId}/datasources/${datasourceId}/data`, 'POST', {
      query: query
    });
  }
}

const server = new Server(
  {
    name: "tableau-mcp-server",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "list_datasources",
        description: "List all published data sources from Tableau",
        inputSchema: {
          type: "object",
          properties: {},
          required: []
        }
      },
      {
        name: "query_datasource", 
        description: "Execute a query against a Tableau data source",
        inputSchema: {
          type: "object",
          properties: {
            datasourceId: {
              type: "string",
              description: "ID of the data source to query"
            },
            query: {
              type: "string", 
              description: "SQL query to execute"
            }
          },
          required: ["datasourceId", "query"]
        }
      }
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const args = request.params.arguments as any;
  const credentials = args.__credentials__;
  
  if (!credentials?.SERVER || !credentials?.PAT_NAME || !credentials?.PAT_VALUE) {
    throw new Error("Missing required Tableau credentials: SERVER, PAT_NAME, PAT_VALUE");
  }

  const client = new TableauClient(
    credentials.SERVER,
    credentials.SITE_NAME || '',
    credentials.PAT_NAME,
    credentials.PAT_VALUE
  );

  try {
    await client.signIn();

    switch (request.params.name) {
      case "list_datasources": {
        const result = await client.listDatasources();
        return {
          content: [{ 
            type: "text", 
            text: JSON.stringify(result, null, 2) 
          }]
        };
      }

      case "query_datasource": {
        const result = await client.queryDatasource(args.datasourceId, args.query);
        return {
          content: [{ 
            type: "text", 
            text: JSON.stringify(result, null, 2) 
          }]
        };
      }

      default:
        throw new Error(`Unknown tool: ${request.params.name}`);
    }
  } catch (error) {
    throw new Error(`Tableau operation failed: ${error instanceof Error ? error.message : String(error)}`);
  }
});

async function runServer() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Tableau MCP Server running on stdio");
}

runServer().catch((error) => {
  console.error("Fatal error in main():", error);
  process.exit(1);
});