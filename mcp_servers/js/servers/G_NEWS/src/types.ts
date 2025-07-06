// 定义Google News API的类型
export interface NewsResult {
  position: number;
  title: string;
  source: {
    name: string;
    icon?: string;
    authors?: string[];
  };
  link: string;
  thumbnail?: string;
  thumbnail_small?: string;
  date?: string;
  snippet?: string;
}

export interface GoogleNewsSearchArgs {
  api_key: string;          // SerpAPI key
  q?: string;               // Search query
  gl?: string;              // Country code
  hl?: string;              // Language code
  topic_token?: string;     // Topic token
  publication_token?: string; // Publication token
  story_token?: string;     // Story token
  section_token?: string;   // Section token
  model_provider?: string;  // AI model provider (openai, gemini)
  __credentials__?: {
    SERP_API_KEY: string;   // SerpAPI key from credentials
  };
}

export function isValidGoogleNewsSearchArgs(args: unknown): args is GoogleNewsSearchArgs {
  if (!args || typeof args !== "object") {
    return false;
  }

  const typedArgs = args as Record<string, unknown>;

  // Check for required api_key
  if (typeof typedArgs.api_key !== "string" || !typedArgs.api_key) {
    return false;
  }

  // Check all optional fields
  if (typedArgs.q !== undefined && typeof typedArgs.q !== "string") return false;
  if (typedArgs.gl !== undefined && typeof typedArgs.gl !== "string") return false;
  if (typedArgs.hl !== undefined && typeof typedArgs.hl !== "string") return false;
  if (typedArgs.topic_token !== undefined && typeof typedArgs.topic_token !== "string") return false;
  if (typedArgs.publication_token !== undefined && typeof typedArgs.publication_token !== "string") return false;
  if (typedArgs.story_token !== undefined && typeof typedArgs.story_token !== "string") return false;
  if (typedArgs.section_token !== undefined && typeof typedArgs.section_token !== "string") return false;
  if (typedArgs.model_provider !== undefined && typeof typedArgs.model_provider !== "string") return false;

  return true;
}

export interface NewsArticle {
  title: string;
  source: string;
  link: string;
  date?: string;
  snippet?: string;
  authors?: string[];
}

export interface NewsCategory {
  name: string;
  articles: NewsArticle[];
  topic_token?: string;
}

export interface MenuLink {
  title: string;
  topic_token: string;
  serpapi_link: string;
}

export interface FormattedNewsResponse {
  categories: NewsCategory[];
  menu_links?: MenuLink[];
  timestamp: string;
}