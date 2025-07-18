#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from 'zod';
import { zodToJsonSchema } from 'zod-to-json-schema';

import * as repository from './operations/repository.js';
import * as files from './operations/files.js';
import * as issues from './operations/issues.js';
import * as pulls from './operations/pulls.js';
import * as branches from './operations/branches.js';
import * as search from './operations/search.js';
import * as commits from './operations/commits.js';
import {
  GitHubError,
  GitHubValidationError,
  GitHubResourceNotFoundError,
  GitHubAuthenticationError,
  GitHubPermissionError,
  GitHubRateLimitError,
  GitHubConflictError,
  isGitHubError,
} from './common/errors.js';
import { VERSION } from "./common/version.js";

const server = new Server(
  {
    name: "github-mcp-server",
    version: VERSION,
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

function formatGitHubError(error: GitHubError): string {
  let message = `GitHub API Error: ${error.message}`;
  
  if (error instanceof GitHubValidationError) {
    message = `Validation Error: ${error.message}`;
    if (error.response) {
      message += `\nDetails: ${JSON.stringify(error.response)}`;
    }
  } else if (error instanceof GitHubResourceNotFoundError) {
    message = `Not Found: ${error.message}`;
  } else if (error instanceof GitHubAuthenticationError) {
    message = `Authentication Failed: ${error.message}`;
  } else if (error instanceof GitHubPermissionError) {
    message = `Permission Denied: ${error.message}`;
  } else if (error instanceof GitHubRateLimitError) {
    message = `Rate Limit Exceeded: ${error.message}\nResets at: ${error.resetAt.toISOString()}`;
  } else if (error instanceof GitHubConflictError) {
    message = `Conflict: ${error.message}`;
  }

  return message;
}

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "create_or_update_file",
        description: "Create or update a single file in a GitHub repository",
        inputSchema: zodToJsonSchema(files.CreateOrUpdateFileSchema),
      },
      {
        name: "search_repositories",
        description: "Search for GitHub repositories",
        inputSchema: zodToJsonSchema(repository.SearchRepositoriesSchema),
      },
      {
        name: "create_repository",
        description: "Create a new GitHub repository in your account",
        inputSchema: zodToJsonSchema(repository.CreateRepositoryOptionsSchema),
      },
      {
        name: "get_file_contents",
        description: "Get the contents of a file or directory from a GitHub repository",
        inputSchema: zodToJsonSchema(files.GetFileContentsSchema),
      },
      {
        name: "push_files",
        description: "Push multiple files to a GitHub repository in a single commit",
        inputSchema: zodToJsonSchema(files.PushFilesSchema),
      },
      {
        name: "create_issue",
        description: "Create a new issue in a GitHub repository",
        inputSchema: zodToJsonSchema(issues.CreateIssueSchema),
      },
      {
        name: "create_pull_request",
        description: "Create a new pull request in a GitHub repository",
        inputSchema: zodToJsonSchema(pulls.CreatePullRequestSchema),
      },
      {
        name: "fork_repository",
        description: "Fork a GitHub repository to your account or specified organization",
        inputSchema: zodToJsonSchema(repository.ForkRepositorySchema),
      },
      {
        name: "create_branch",
        description: "Create a new branch in a GitHub repository",
        inputSchema: zodToJsonSchema(branches.CreateBranchSchema),
      },
      {
        name: "list_commits",
        description: "Get list of commits of a branch in a GitHub repository",
        inputSchema: zodToJsonSchema(commits.ListCommitsSchema)
      },
      {
        name: "list_issues",
        description: "List issues in a GitHub repository with filtering options",
        inputSchema: zodToJsonSchema(issues.ListIssuesOptionsSchema)
      },
      {
        name: "update_issue",
        description: "Update an existing issue in a GitHub repository",
        inputSchema: zodToJsonSchema(issues.UpdateIssueOptionsSchema)
      },
      {
        name: "add_issue_comment",
        description: "Add a comment to an existing issue",
        inputSchema: zodToJsonSchema(issues.IssueCommentSchema)
      },
      {
        name: "search_code",
        description: "Search for code across GitHub repositories",
        inputSchema: zodToJsonSchema(search.SearchCodeSchema),
      },
      {
        name: "search_issues",
        description: "Search for issues and pull requests across GitHub repositories",
        inputSchema: zodToJsonSchema(search.SearchIssuesSchema),
      },
      {
        name: "search_users",
        description: "Search for users on GitHub",
        inputSchema: zodToJsonSchema(search.SearchUsersSchema),
      },
      {
        name: "get_issue",
        description: "Get details of a specific issue in a GitHub repository.",
        inputSchema: zodToJsonSchema(issues.GetIssueSchema)
      },
      {
        name: "get_pull_request",
        description: "Get details of a specific pull request",
        inputSchema: zodToJsonSchema(pulls.GetPullRequestSchema)
      },
      {
        name: "list_pull_requests",
        description: "List and filter repository pull requests",
        inputSchema: zodToJsonSchema(pulls.ListPullRequestsSchema)
      },
      {
        name: "create_pull_request_review",
        description: "Create a review on a pull request",
        inputSchema: zodToJsonSchema(pulls.CreatePullRequestReviewSchema)
      },
      {
        name: "merge_pull_request",
        description: "Merge a pull request",
        inputSchema: zodToJsonSchema(pulls.MergePullRequestSchema)
      },
      {
        name: "get_pull_request_files",
        description: "Get the list of files changed in a pull request",
        inputSchema: zodToJsonSchema(pulls.GetPullRequestFilesSchema)
      },
      {
        name: "get_pull_request_status",
        description: "Get the combined status of all status checks for a pull request",
        inputSchema: zodToJsonSchema(pulls.GetPullRequestStatusSchema)
      },
      {
        name: "update_pull_request_branch",
        description: "Update a pull request branch with the latest changes from the base branch",
        inputSchema: zodToJsonSchema(pulls.UpdatePullRequestBranchSchema)
      },
      {
        name: "get_pull_request_comments",
        description: "Get the review comments on a pull request",
        inputSchema: zodToJsonSchema(pulls.GetPullRequestCommentsSchema)
      },
      {
        name: "get_pull_request_reviews",
        description: "Get the reviews on a pull request",
        inputSchema: zodToJsonSchema(pulls.GetPullRequestReviewsSchema)
      }
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  try {
    if (!request.params.arguments) {
      throw new Error("Arguments are required");
    }

    // Extract credentials from arguments
    const args = request.params.arguments as any;
    const token = args.__credentials__?.GITHUB_PERSONAL_ACCESS_TOKEN;

    // Helper functions for standardized responses
    const createSuccessResponse = (operation: string, message: string, data: any, metadata: any = {}) => {
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            success: true,
            operation,
            message,
            data,
            metadata: {
              timestamp: new Date().toISOString(),
              ...metadata
            }
          }, null, 2)
        }]
      };
    };

    const createErrorResponse = (operation: string, message: string, error: any, suggestions: string[] = []) => {
      return {
        content: [{
          type: "text", 
          text: JSON.stringify({
            success: false,
            operation,
            message,
            error: error.message || error,
            suggestions,
            metadata: {
              timestamp: new Date().toISOString()
            }
          }, null, 2)
        }]
      };
    };

    switch (request.params.name) {
      case "fork_repository": {
        const args = repository.ForkRepositorySchema.parse(request.params.arguments);
        const fork = await repository.forkRepository({ ...args, __credentials__: { GITHUB_PERSONAL_ACCESS_TOKEN: token } });
        return {
          content: [{ type: "text", text: JSON.stringify(fork, null, 2) }],
        };
      }

      case "create_branch": {
        const args = branches.CreateBranchSchema.parse(request.params.arguments);
        const branch = await branches.createBranchFromRef(
          args.owner,
          args.repo,
          args.branch,
          args.from_branch,
          token
        );
        return {
          content: [{ type: "text", text: JSON.stringify(branch, null, 2) }],
        };
      }

      case "search_repositories": {
        const args = repository.SearchRepositoriesSchema.parse(request.params.arguments);
        const results = await repository.searchRepositories({ ...args, __credentials__: { GITHUB_PERSONAL_ACCESS_TOKEN: token } });
        return {
          content: [{ type: "text", text: JSON.stringify(results, null, 2) }],
        };
      }

      case "create_repository": {
        const args = repository.CreateRepositoryOptionsSchema.parse(request.params.arguments);
        const result = await repository.createRepository({ ...args, __credentials__: { GITHUB_PERSONAL_ACCESS_TOKEN: token } });
        return {
          content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
        };
      }

      case "get_file_contents": {
        const args = files.GetFileContentsSchema.parse(request.params.arguments);
        const contents = await files.getFileContents(
          args.owner,
          args.repo,
          args.path,
          args.branch,
          token
        );
        return {
          content: [{ type: "text", text: JSON.stringify(contents, null, 2) }],
        };
      }

      case "create_or_update_file": {
        const args = files.CreateOrUpdateFileSchema.parse(request.params.arguments);
        const result = await files.createOrUpdateFile(
          args.owner,
          args.repo,
          args.path,
          args.content,
          args.message,
          args.branch,
          args.sha,
          token
        );
        return {
          content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
        };
      }

      case "push_files": {
        const args = files.PushFilesSchema.parse(request.params.arguments);
        const result = await files.pushFiles(
          args.owner,
          args.repo,
          args.branch,
          args.files,
          args.message,
          token
        );
        return {
          content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
        };
      }

      case "create_issue": {
        const args = issues.CreateIssueSchema.parse(request.params.arguments);
        const { owner, repo, ...options } = args;
        const issue = await issues.createIssue(owner, repo, options, token);
        return {
          content: [{ type: "text", text: JSON.stringify(issue, null, 2) }],
        };
      }

      case "create_pull_request": {
        const args = pulls.CreatePullRequestSchema.parse(request.params.arguments);
        const pullRequest = await pulls.createPullRequest({ ...args, __credentials__: { GITHUB_PERSONAL_ACCESS_TOKEN: token } });
        return {
          content: [{ type: "text", text: JSON.stringify(pullRequest, null, 2) }],
        };
      }

      case "search_code": {
        const args = search.SearchCodeSchema.parse(request.params.arguments);
        const results = await search.searchCode({ ...args, __credentials__: { GITHUB_PERSONAL_ACCESS_TOKEN: token } });
        return {
          content: [{ type: "text", text: JSON.stringify(results, null, 2) }],
        };
      }

      case "search_issues": {
        const args = search.SearchIssuesSchema.parse(request.params.arguments);
        const results = await search.searchIssues({ ...args, __credentials__: { GITHUB_PERSONAL_ACCESS_TOKEN: token } });
        return {
          content: [{ type: "text", text: JSON.stringify(results, null, 2) }],
        };
      }

      case "search_users": {
        const args = search.SearchUsersSchema.parse(request.params.arguments);
        const results = await search.searchUsers({ ...args, __credentials__: { GITHUB_PERSONAL_ACCESS_TOKEN: token } });
        return {
          content: [{ type: "text", text: JSON.stringify(results, null, 2) }],
        };
      }

      case "list_issues": {
        const args = issues.ListIssuesOptionsSchema.parse(request.params.arguments);
        const { owner, repo, ...options } = args;
        const result = await issues.listIssues(owner, repo, options, token);
        return {
          content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
        };
      }

      case "update_issue": {
        const args = issues.UpdateIssueOptionsSchema.parse(request.params.arguments);
        const { owner, repo, issue_number, ...options } = args;
        const result = await issues.updateIssue(owner, repo, issue_number, options, token);
        return {
          content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
        };
      }

      case "add_issue_comment": {
        const args = issues.IssueCommentSchema.parse(request.params.arguments);
        const { owner, repo, issue_number, body } = args;
        const result = await issues.addIssueComment(owner, repo, issue_number, body, token);
        return {
          content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
        };
      }

      case "list_commits": {
        const args = commits.ListCommitsSchema.parse(request.params.arguments);
        try {
          const results = await commits.listCommits({ ...args, __credentials__: { GITHUB_PERSONAL_ACCESS_TOKEN: token } });
          return createSuccessResponse(
            "list_commits",
            `Successfully retrieved ${Array.isArray(results) ? results.length : "unknown number of"} commits from ${args.owner}/${args.repo}`,
            results,
            {
              repository: `${args.owner}/${args.repo}`,
              branch: args.sha || "default branch",
              commit_count: Array.isArray(results) ? results.length : 0,
              page: args.page || 1,
              per_page: args.perPage || 30
            }
          );
        } catch (error: any) {
          return createErrorResponse(
            "list_commits",
            `Failed to retrieve commits from ${args.owner}/${args.repo}`,
            error,
            [
              "Check if the repository exists and is accessible",
              "Verify the branch/SHA exists",
              "Ensure your GitHub token has read access to the repository"
            ]
          );
        }
      }

      case "get_issue": {
        const args = issues.GetIssueSchema.parse(request.params.arguments);
        const issue = await issues.getIssue(args.owner, args.repo, args.issue_number, token);
        return {
          content: [{ type: "text", text: JSON.stringify(issue, null, 2) }],
        };
      }

      case "get_pull_request": {
        const args = pulls.GetPullRequestSchema.parse(request.params.arguments);
        const pullRequest = await pulls.getPullRequest(args.owner, args.repo, args.pull_number, token);
        return {
          content: [{ type: "text", text: JSON.stringify(pullRequest, null, 2) }],
        };
      }

      case "list_pull_requests": {
        const args = pulls.ListPullRequestsSchema.parse(request.params.arguments);
        const { owner, repo, ...options } = args;
        const pullRequests = await pulls.listPullRequests(owner, repo, options, token);
        return {
          content: [{ type: "text", text: JSON.stringify(pullRequests, null, 2) }],
        };
      }

      case "create_pull_request_review": {
        const args = pulls.CreatePullRequestReviewSchema.parse(request.params.arguments);
        const { owner, repo, pull_number, ...options } = args;
        const review = await pulls.createPullRequestReview(owner, repo, pull_number, options, token);
        return {
          content: [{ type: "text", text: JSON.stringify(review, null, 2) }],
        };
      }

      case "merge_pull_request": {
        const args = pulls.MergePullRequestSchema.parse(request.params.arguments);
        const { owner, repo, pull_number, ...options } = args;
        try {
          const result = await pulls.mergePullRequest(owner, repo, pull_number, options, token);
          
          // Enhanced response with clear success indication
          const enhancedResponse = {
            success: true,
            message: `Pull request #${pull_number} has been successfully merged`,
            merge_details: result,
            repository: `${owner}/${repo}`,
            pull_request_number: pull_number,
            merged_at: new Date().toISOString()
          };
          
          // Debug logging
          console.error("DEBUG - MERGE SUCCESS RESPONSE:", JSON.stringify(enhancedResponse, null, 2));
          
          return {
            content: [{ 
              type: "text", 
              text: JSON.stringify(enhancedResponse, null, 2) 
            }],
          };
        } catch (error: any) {
          // Enhanced error response
          const errorResponse = {
            success: false,
            message: `Failed to merge pull request #${pull_number}`,
            error: error.message || error,
            repository: `${owner}/${repo}`,
            pull_request_number: pull_number,
            possible_reasons: [
              "Pull request is not mergeable (conflicts, checks failing, etc.)",
              "Insufficient permissions", 
              "Pull request is already merged or closed",
              "Branch protection rules prevent merging"
            ]
          };
          
          // Debug logging
          console.error("DEBUG - MERGE ERROR RESPONSE:", JSON.stringify(errorResponse, null, 2));
          
          return {
            content: [{ 
              type: "text", 
              text: JSON.stringify(errorResponse, null, 2) 
            }],
          };
        }
      }

      case "get_pull_request_files": {
        const args = pulls.GetPullRequestFilesSchema.parse(request.params.arguments);
        const files = await pulls.getPullRequestFiles(args.owner, args.repo, args.pull_number, token);
        return {
          content: [{ type: "text", text: JSON.stringify(files, null, 2) }],
        };
      }

      case "get_pull_request_status": {
        const args = pulls.GetPullRequestStatusSchema.parse(request.params.arguments);
        const status = await pulls.getPullRequestStatus(args.owner, args.repo, args.pull_number, token);
        return {
          content: [{ type: "text", text: JSON.stringify(status, null, 2) }],
        };
      }

      case "update_pull_request_branch": {
        const args = pulls.UpdatePullRequestBranchSchema.parse(request.params.arguments);
        const { owner, repo, pull_number, expected_head_sha } = args;
        await pulls.updatePullRequestBranch(owner, repo, pull_number, expected_head_sha, token);
        return {
          content: [{ type: "text", text: JSON.stringify({ success: true }, null, 2) }],
        };
      }

      case "get_pull_request_comments": {
        const args = pulls.GetPullRequestCommentsSchema.parse(request.params.arguments);
        const comments = await pulls.getPullRequestComments(args.owner, args.repo, args.pull_number, token);
        return {
          content: [{ type: "text", text: JSON.stringify(comments, null, 2) }],
        };
      }

      case "get_pull_request_reviews": {
        const args = pulls.GetPullRequestReviewsSchema.parse(request.params.arguments);
        const reviews = await pulls.getPullRequestReviews(args.owner, args.repo, args.pull_number, token);
        return {
          content: [{ type: "text", text: JSON.stringify(reviews, null, 2) }],
        };
      }

      default:
        throw new Error(`Unknown tool: ${request.params.name}`);
    }
  } catch (error) {
    if (error instanceof z.ZodError) {
      throw new Error(`Invalid input: ${JSON.stringify(error.errors)}`);
    }
    if (isGitHubError(error)) {
      throw new Error(formatGitHubError(error));
    }
    throw error;
  }
});

async function runServer() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("GitHub MCP Server running on stdio");
}

runServer().catch((error) => {
  console.error("Fatal error in main():", error);
  process.exit(1);
});
