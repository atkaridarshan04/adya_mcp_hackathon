# Google News MCP Server Features

## Overview

A Model Context Protocol server that enables AI assistants to search and retrieve news articles from Google News using the SerpAPI.

## Available Tools

### News Search
- **google_news_search**: Search Google News for articles and news content.

## Key Features

### Comprehensive News Search
- Search news articles by keyword (`q`).
- Filter news by country (`gl`) and language (`hl`).
- Search for specific news topics using `topic_token`.
- Find articles from particular publications using `publication_token`.
- Retrieve full coverage of a story using `story_token`.
- Filter news by specific sections using `section_token`.

### AI-Powered Result Processing
- Option to process search results with an AI model for summarization or analysis.
- Automatically categorizes news results by topic (e.g., AI & Technology, Business, Science & Research, Healthcare).

## Prerequisites

- Node.js v18 or higher
- SerpAPI key
- (Optional) OpenAI API key or Gemini API key for AI processing

## Authentication

- SerpAPI key is required for all news search operations.