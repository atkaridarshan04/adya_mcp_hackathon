//evals.ts

import { EvalConfig } from 'mcp-evals';
import { openai } from "@ai-sdk/openai";
import { grade, EvalFunction } from "mcp-evals";

const google_news_searchEval: EvalFunction = {
    name: 'google_news_search Evaluation',
    description: 'Evaluates the functionality and correctness of google_news_search calls',
    run: async () => {
        const result = await grade(openai("gpt-4"), "Search for the latest headlines about space exploration in the US, in English, and categorize them by topic. Include any relevant publication tokens if available.");
        return JSON.parse(result);
    }
};

const config: EvalConfig = {
    model: openai("gpt-4"),
    evals: [google_news_searchEval]
};
  
export default config;
  
export const evals = [google_news_searchEval];