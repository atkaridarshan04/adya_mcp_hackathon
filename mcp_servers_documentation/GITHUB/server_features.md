# GitHub MCP Server - Server Features

## Overview

A Model Context Protocol server that enables AI assistants to interact with GitHub repositories through the GitHub REST API. This server provides tools for managing repositories, files, issues, pull requests, and search functionality.

## Available Tools

### File Operations
- **create_or_update_file**: Create or update a single file in a repository
- **get_file_contents**: Get contents of a file or directory from a repository
- **push_files**: Push multiple files to a repository in a single commit

### Repository Management
- **search_repositories**: Search for GitHub repositories
- **create_repository**: Create a new GitHub repository
- **fork_repository**: Fork a repository to your account or organization

### Branch Operations
- **create_branch**: Create a new branch in a repository
- **list_commits**: Get list of commits of a branch in a repository

### Issue Management
- **create_issue**: Create a new issue in a repository
- **get_issue**: Get details of a specific issue
- **list_issues**: List issues in a repository with filtering options
- **update_issue**: Update an existing issue
- **add_issue_comment**: Add a comment to an existing issue

### Pull Request Operations
- **create_pull_request**: Create a new pull request in a repository

### Search Functionality
- **search_code**: Search for code across GitHub repositories
- **search_issues**: Search for issues and pull requests
- **search_users**: Search for users on GitHub

## Key Features

### File Management
- Single file creation and updates with proper Git history
- Batch file operations in single commits
- File content retrieval and parsing
- Automatic branch creation for operations

### Repository Operations
- Repository creation with full configuration
- Repository search with advanced filters
- Fork repositories with customization options
- Repository information retrieval

### Issue Tracking
- Complete issue lifecycle management
- Issue search and filtering capabilities
- Comment management on issues
- Issue status and metadata updates

### Collaboration Features
- Pull request creation and management
- Branch management for collaboration
- Code search across repositories
- User and organization search

## Prerequisites

- Node.js v18 or higher
- GitHub account with appropriate permissions
- GitHub Personal Access Token
- Network access to GitHub API

## Authentication

- Personal Access Tokens for user authentication
- Fine-grained access control support
- Repository-level permissions
- Organization access management
