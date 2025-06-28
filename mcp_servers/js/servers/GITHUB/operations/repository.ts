import { z } from "zod";
import { githubRequest } from "../common/utils.js";
import { GitHubRepositorySchema, GitHubSearchResponseSchema } from "../common/types.js";

// Schema definitions
export const CreateRepositoryOptionsSchema = z.object({
  name: z.string().describe("Repository name"),
  description: z.string().optional().describe("Repository description"),
  private: z.boolean().optional().describe("Whether the repository should be private"),
  autoInit: z.boolean().optional().describe("Initialize with README.md"),
  __credentials__: z.object({
    GITHUB_PERSONAL_ACCESS_TOKEN: z.string()
  }).optional().describe("GitHub credentials")
});

export const SearchRepositoriesSchema = z.object({
  query: z.string().describe("Search query (see GitHub search syntax)"),
  page: z.number().optional().describe("Page number for pagination (default: 1)"),
  perPage: z.number().optional().describe("Number of results per page (default: 30, max: 100)"),
  __credentials__: z.object({
    GITHUB_PERSONAL_ACCESS_TOKEN: z.string()
  }).optional().describe("GitHub credentials")
});

export const ForkRepositorySchema = z.object({
  owner: z.string().describe("Repository owner (username or organization)"),
  repo: z.string().describe("Repository name"),
  organization: z.string().optional().describe("Optional: organization to fork to (defaults to your personal account)"),
  __credentials__: z.object({
    GITHUB_PERSONAL_ACCESS_TOKEN: z.string()
  }).optional().describe("GitHub credentials")
});

// Type exports
export type CreateRepositoryOptions = z.infer<typeof CreateRepositoryOptionsSchema>;

// Function implementations
export async function createRepository(options: CreateRepositoryOptions) {
  const token = options.__credentials__?.GITHUB_PERSONAL_ACCESS_TOKEN;
  const { __credentials__, ...repoOptions } = options;
  
  const response = await githubRequest("https://api.github.com/user/repos", {
    method: "POST",
    body: repoOptions,
  }, token);
  return GitHubRepositorySchema.parse(response);
}

export async function searchRepositories(params: z.infer<typeof SearchRepositoriesSchema>) {
  const { query, page = 1, perPage = 30, __credentials__ } = params;
  const token = __credentials__?.GITHUB_PERSONAL_ACCESS_TOKEN;
  
  const url = new URL("https://api.github.com/search/repositories");
  url.searchParams.append("q", query);
  url.searchParams.append("page", page.toString());
  url.searchParams.append("per_page", perPage.toString());

  const response = await githubRequest(url.toString(), {}, token);
  return GitHubSearchResponseSchema.parse(response);
}

export async function forkRepository(params: z.infer<typeof ForkRepositorySchema>) {
  const { owner, repo, organization, __credentials__ } = params;
  const token = __credentials__?.GITHUB_PERSONAL_ACCESS_TOKEN;
  
  const url = organization
    ? `https://api.github.com/repos/${owner}/${repo}/forks?organization=${organization}`
    : `https://api.github.com/repos/${owner}/${repo}/forks`;

  const response = await githubRequest(url, { method: "POST" }, token);
  return GitHubRepositorySchema.extend({
    parent: GitHubRepositorySchema,
    source: GitHubRepositorySchema,
  }).parse(response);
}
