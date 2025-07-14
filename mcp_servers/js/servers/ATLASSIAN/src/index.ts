#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import axios from 'axios';

const server = new Server({
  name: 'atlassian-mcp-server',
  version: '1.0.0',
}, {
  capabilities: { tools: {} },
});

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: 'get_cards_by_list_id',
      description: 'Fetch cards from a specific Trello list',
      inputSchema: {
        type: 'object',
        properties: {
          listId: { type: 'string', description: 'ID of the Trello list' },
        },
        required: ['listId'],
      },
    },
    {
      name: 'get_lists',
      description: 'Retrieve all lists from the specified board',
      inputSchema: { type: 'object', properties: {}, required: [] },
    },
    {
      name: 'add_card_to_list',
      description: 'Add a new card to a specified list',
      inputSchema: {
        type: 'object',
        properties: {
          listId: { type: 'string', description: 'ID of the list to add the card to' },
          name: { type: 'string', description: 'Name of the card' },
          description: { type: 'string', description: 'Description of the card' },
        },
        required: ['listId', 'name'],
      },
    },
    {
      name: 'update_card_details',
      description: 'Update an existing card details',
      inputSchema: {
        type: 'object',
        properties: {
          cardId: { type: 'string', description: 'ID of the card to update' },
          name: { type: 'string', description: 'New name for the card' },
          description: { type: 'string', description: 'New description for the card' },
        },
        required: ['cardId'],
      },
    },
    {
      name: 'list_boards',
      description: 'List all boards the user has access to',
      inputSchema: { type: 'object', properties: {}, required: [] },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const args = request.params.arguments as any;
  const creds = args.__credentials__ || {};
  const { TRELLO_API_KEY, TRELLO_TOKEN, TRELLO_BOARD_ID } = creds;

  if (!TRELLO_API_KEY || !TRELLO_TOKEN) {
    return { content: [{ type: 'text', text: JSON.stringify({ error: 'Missing Trello credentials' }) }] };
  }

  const api = axios.create({
    baseURL: 'https://api.trello.com/1',
    params: { key: TRELLO_API_KEY, token: TRELLO_TOKEN },
  });

  try {
    switch (request.params.name) {
      case 'get_cards_by_list_id': {
        const response = await api.get(`/lists/${args.listId}/cards`);
        return { content: [{ type: 'text', text: JSON.stringify(response.data) }] };
      }
      case 'get_lists': {
        const response = await api.get(`/boards/${TRELLO_BOARD_ID}/lists`);
        return { content: [{ type: 'text', text: JSON.stringify(response.data) }] };
      }
      case 'add_card_to_list': {
        const response = await api.post('/cards', {
          idList: args.listId,
          name: args.name,
          desc: args.description,
        });
        return { content: [{ type: 'text', text: JSON.stringify(response.data) }] };
      }
      case 'update_card_details': {
        const response = await api.put(`/cards/${args.cardId}`, {
          name: args.name,
          desc: args.description,
        });
        return { content: [{ type: 'text', text: JSON.stringify(response.data) }] };
      }
      case 'list_boards': {
        const response = await api.get('/members/me/boards');
        return { content: [{ type: 'text', text: JSON.stringify(response.data) }] };
      }
      default:
        throw new Error(`Unknown tool: ${request.params.name}`);
    }
  } catch (error: any) {
    return { content: [{ type: 'text', text: JSON.stringify({ error: error.message }) }] };
  }
});

async function runServer() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Atlassian MCP Server running on stdio');
}

runServer().catch(console.error);