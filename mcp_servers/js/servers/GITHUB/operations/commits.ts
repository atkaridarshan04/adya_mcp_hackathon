import { z } from "zod";
import { githubRequest, buildUrl } from "../common/utils.js";

export const ListCommitsSchema = z.object({
  owner: z.string(),
  repo: z.string(),
  sha: z.string().optional(),
  page: z.number().optional(),
  perPage: z.number().optional(),
  __credentials__: z.object({
    GITHUB_PERSONAL_ACCESS_TOKEN: z.string()
  }).optional().describe("GitHub credentials")
});

export async function listCommits(params: z.infer<typeof ListCommitsSchema>) {
  const { owner, repo, page, perPage, sha, __credentials__ } = params;
  const token = __credentials__?.GITHUB_PERSONAL_ACCESS_TOKEN;
  
  return githubRequest(
    buildUrl(`https://api.github.com/repos/${owner}/${repo}/commits`, {
      page: page?.toString(),
      per_page: perPage?.toString(),
      sha
    }),
    {},
    token
  );
}