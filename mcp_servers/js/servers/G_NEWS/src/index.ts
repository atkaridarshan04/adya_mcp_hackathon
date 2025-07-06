#!/usr/bin/env node
import 'dotenv/config';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
  ErrorCode,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import axios from 'axios';
import {
  GoogleNewsSearchArgs,
  isValidGoogleNewsSearchArgs,
  NewsArticle,
  NewsCategory,
  FormattedNewsResponse,
  MenuLink
} from './types.js';

// SerpAPI configuration
const SERP_API_BASE_URL = 'https://serpapi.com/search';

// Dynamic credentials will be passed during tool calls

class GoogleNewsServer {
  private server: Server;
  private axiosInstance: import('axios').AxiosInstance;

  constructor() {
    this.server = new Server(
      {
        name: 'google-news-server', 
        version: '1.0.0'
      },
      {
        capabilities: { tools: {} }
      }
    );

    this.axiosInstance = axios.create({
      baseURL: SERP_API_BASE_URL,
    });

    this.setupHandlers();
    this.setupErrorHandling();
  }

  private setupErrorHandling(): void {
    this.server.onerror = (error) => {
      console.error('[MCP Error]', error);
    };

    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  private setupHandlers(): void {
    // Register available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'google_news_search',
          description: 'Search Google News for articles and news content. Results will be automatically categorized by topic.',
          inputSchema: {
            type: 'object',
            properties: {
              api_key: {
                type: 'string',
                description: 'SerpAPI key for accessing Google News',
              },
              q: {
                type: 'string',
                description: 'Search query',
              },
              gl: {
                type: 'string',
                description: 'Country code (e.g., us, uk)',
                default: 'us'
              },
              hl: {
                type: 'string',
                description: 'Language code (e.g., en)',
                default: 'en'
              },
              topic_token: {
                type: 'string',
                description: 'Topic token for specific news topics',
              },
              publication_token: {
                type: 'string',
                description: 'Publication token for specific publishers',
              },
              story_token: {
                type: 'string',
                description: 'Story token for full coverage of a story',
              },
              section_token: {
                type: 'string',
                description: 'Section token for specific sections',
              },
              model_provider: {
                type: 'string',
                description: 'AI model provider to use for processing results (openai, gemini)',
                default: 'none'
              },
            },
            required: ['api_key']
          },
        },
      ],
    }));

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      if (name === 'google_news_search') {
        // Extract API key from __credentials__ if present
        const typedArgs = args as any;
        if (typedArgs.__credentials__ && typedArgs.__credentials__.SERP_API_KEY) {
          typedArgs.api_key = typedArgs.__credentials__.SERP_API_KEY;
          delete typedArgs.__credentials__;
        }
        
        // Use the typed args for the rest of the function
        const googleNewsArgs = typedArgs as GoogleNewsSearchArgs;
        
        if (!isValidGoogleNewsSearchArgs(googleNewsArgs)) {
          throw new McpError(
            ErrorCode.InvalidParams,
            'Invalid arguments for google_news_search'
          );
        }

        // Check for required API key
        if (!googleNewsArgs.api_key) {
          throw new McpError(
            ErrorCode.InvalidParams,
            'API key is required for google_news_search'
          );
        }

        const params = {
          ...googleNewsArgs,
          engine: 'google_news',
          api_key: googleNewsArgs.api_key,
          gl: googleNewsArgs.gl || 'us',
          hl: googleNewsArgs.hl === 'zh' ? 'en' : (googleNewsArgs.hl || 'en')
        };

        // Remove model_provider from params to avoid sending it to SerpAPI
        const modelProvider = googleNewsArgs.model_provider || 'none';
        delete params.model_provider;

        try {
          const response = await this.axiosInstance.get('', { params });
          const formattedResults = this.formatNewsResults(response.data);
          let resultText = this.formatResponseText(formattedResults);

          // Process results with AI model if specified
          if (modelProvider !== 'none') {
            try {
              resultText = await this.processResultsWithAI(resultText, modelProvider, googleNewsArgs.api_key);
            } catch (aiError) {
              console.error('AI processing error:', aiError);
              // Continue with original formatted results if AI processing fails
            }
          }

          return {
            content: [{
              type: 'text',
              text: resultText
            }]
          };
        } catch (error) {
          return {
            isError: true,
            content: [{
              type: 'text',
              text: this.getErrorMessage(error)
            }]
          };
        }
      }

      throw new McpError(
        ErrorCode.MethodNotFound,
        `Unknown tool: ${name}`
      );
    });
  }

  private formatNewsResults(data: any): FormattedNewsResponse {
    const newsResults = data.news_results || [];
    const menuLinks = data.menu_links || [];
    const categories = new Map<string, NewsArticle[]>();
    
    // Categorize news based on content
    newsResults.forEach((result: any) => {
      let category = 'General';
      
      // Categorize by keywords in title and snippet
      const titleAndSnippet = (result.title + ' ' + (result.snippet || '')).toLowerCase();
      
      if (titleAndSnippet.match(/ai|artificial intelligence|machine learning|deep learning/)) {
        category = 'AI & Technology';
      } else if (titleAndSnippet.match(/business|economy|market|finance/)) {
        category = 'Business';
      } else if (titleAndSnippet.match(/science|research|study|discovery/)) {
        category = 'Science & Research';
      } else if (titleAndSnippet.match(/health|medical|disease|treatment/)) {
        category = 'Healthcare';
      }
      
      if (!categories.has(category)) {
        categories.set(category, []);
      }
      
      categories.get(category)?.push({
        title: result.title,
        source: result.source.name,
        link: result.link,
        date: result.date,
        snippet: result.snippet,
        authors: result.source.authors
      });
    });
    
    // Convert to final format
    const formattedCategories: NewsCategory[] = Array.from(categories.entries())
      .map(([name, articles]) => ({
        name,
        articles: articles.sort((a, b) => {
          // Sort by date in descending order
          const dateA = a.date ? new Date(a.date) : new Date(0);
          const dateB = b.date ? new Date(b.date) : new Date(0);
          return dateB.getTime() - dateA.getTime();
        })
      }));

    return {
      categories: formattedCategories,
      menu_links: menuLinks,
      timestamp: new Date().toISOString()
    };
  }

  private formatResponseText(formattedResults: FormattedNewsResponse): string {
    const categoryTexts = formattedResults.categories
      .map(category => {
        const articlesList = category.articles
          .map(article => {
            let text = `- ${article.title}\n`;
            text += `  Source: ${article.source}\n`;
            if (article.authors?.length) {
              text += `  Authors: ${article.authors.join(', ')}\n`;
            }
            if (article.snippet) {
              text += `  Summary: ${article.snippet}\n`;
            }
            if (article.date) {
              text += `  Date: ${article.date}\n`;
            }
            text += `  Link: ${article.link}`;
            return text;
          })
          .join('\n\n');
          
        return `${category.name} (${category.articles.length} articles):\n${articlesList}`;
      })
      .join('\n\n' + '='.repeat(80) + '\n\n');

    return categoryTexts;
  }

  private getErrorMessage(error: any): string {
    if (axios.isAxiosError(error)) {
      if (error.response?.data?.error === "Unsupported `zh` interface language - hl parameter.") {
        return "Sorry, Google News API doesn't support Chinese interface. Automatically switched to English display.";
      }
      return `API Error: ${error.response?.data?.error || error.message}`;
    }
    return `Unknown error: ${error.message || 'Please try again later'}`;
  }

  private async processResultsWithAI(resultText: string, modelProvider: string, apiKey: string): Promise<string> {
    const prompt = `You are a news analyst. Analyze and summarize the following news articles, highlighting key trends, important developments, and connections between stories. Format your response in a clear, concise way that helps the reader understand the most important information:

${resultText}`;
    
    try {
      if (modelProvider === 'openai') {
        return await this.processWithOpenAI(prompt, apiKey);
      } else if (modelProvider === 'gemini') {
        return await this.processWithGemini(prompt, apiKey);
      } else {
        throw new Error(`Unsupported model provider: ${modelProvider}`);
      }
    } catch (error) {
      console.error(`Error processing with ${modelProvider}:`, error);
      throw error;
    }
  }

  private async processWithOpenAI(prompt: string, apiKey: string): Promise<string> {
    try {
      const response = await axios.post(
        'https://api.openai.com/v1/chat/completions',
        {
          model: 'gpt-3.5-turbo',
          messages: [
            { role: 'system', content: 'You are a helpful news analyst assistant.' },
            { role: 'user', content: prompt }
          ],
          temperature: 0.3,
          max_tokens: 1000
        },
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${apiKey}`
          }
        }
      );
      
      return response.data.choices[0].message.content;
    } catch (error) {
      console.error('OpenAI processing error:', error);
      throw error;
    }
  }

  private async processWithGemini(prompt: string, apiKey: string): Promise<string> {
    try {
      const response = await axios.post(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key=${apiKey}`,
        {
          contents: [
            {
              role: 'user',
              parts: [{ text: prompt }]
            }
          ],
          generationConfig: {
            temperature: 0.3,
            maxOutputTokens: 1000
          }
        },
        {
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );
      
      return response.data.candidates[0].content.parts[0].text;
    } catch (error) {
      console.error('Gemini processing error:', error);
      throw error;
    }
  }

  async run(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
  }
}

// Create and start the server
const server = new GoogleNewsServer();
server.run().catch(console.error);