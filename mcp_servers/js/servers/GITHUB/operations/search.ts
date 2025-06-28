import { z } from "zod";
import { githubRequest, buildUrl } from "../common/utils.js";

export const SearchOptions = z.object({
  q: z.string(),
  order: z.enum(["asc", "desc"]).optional(),
  page: z.number().min(1).optional(),
  per_page: z.number().min(1).max(100).optional(),
});

export const SearchUsersOptions = SearchOptions.extend({
  sort: z.enum(["followers", "repositories", "joined"]).optional(),
});

export const SearchIssuesOptions = SearchOptions.extend({
  sort: z.enum([
    "comments",
    "reactions",
    "reactions-+1",
    "reactions--1",
    "reactions-smile",
    "reactions-thinking_face",
    "reactions-heart",
    "reactions-tada",
    "interactions",
    "created",
    "updated",
  ]).optional(),
});

export const SearchCodeSchema = SearchOptions.extend({
  __credentials__: z.object({
    GITHUB_PERSONAL_ACCESS_TOKEN: z.string()
  }).optional().describe("GitHub credentials")
});
export const SearchUsersSchema = SearchUsersOptions.extend({
  __credentials__: z.object({
    GITHUB_PERSONAL_ACCESS_TOKEN: z.string()
  }).optional().describe("GitHub credentials")
});
export const SearchIssuesSchema = SearchIssuesOptions.extend({
  __credentials__: z.object({
    GITHUB_PERSONAL_ACCESS_TOKEN: z.string()
  }).optional().describe("GitHub credentials")
});

export async function searchCode(params: z.infer<typeof SearchCodeSchema>) {
  const { __credentials__, ...searchParams } = params;
  const token = __credentials__?.GITHUB_PERSONAL_ACCESS_TOKEN;
  return githubRequest(buildUrl("https://api.github.com/search/code", searchParams), {}, token);
}

export async function searchIssues(params: z.infer<typeof SearchIssuesSchema>) {
  const { __credentials__, ...searchParams } = params;
  const token = __credentials__?.GITHUB_PERSONAL_ACCESS_TOKEN;
  return githubRequest(buildUrl("https://api.github.com/search/issues", searchParams), {}, token);
}

export async function searchUsers(params: z.infer<typeof SearchUsersSchema>) {
  const { __credentials__, ...searchParams } = params;
  const token = __credentials__?.GITHUB_PERSONAL_ACCESS_TOKEN;
  return githubRequest(buildUrl("https://api.github.com/search/users", searchParams), {}, token);
}