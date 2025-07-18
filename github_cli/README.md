# GitHub CLI Tools

A flexible GitHub CLI wrapper tool for Kubiya, providing AI-controlled access to all GitHub CLI functionality.

## Overview

This package provides a single, flexible tool that wraps the GitHub CLI (`gh`) command-line interface, allowing AI agents to execute any GitHub CLI command through the Kubiya platform. Instead of multiple specific tools, this approach gives AI full control over the GitHub CLI.

## Features

- **Full GitHub CLI Access**: Execute any `gh` command through a single tool
- **AI-Friendly**: Let AI construct the exact commands it needs
- **Flexible**: Supports all current and future GitHub CLI commands
- **Simple**: One tool instead of multiple specific tools
- **Authenticated**: Automatic GitHub authentication handling

## Available Tool

### `github_cli`
Execute any GitHub CLI command by passing the command as an argument.

**Parameters:**
- `command` (required): The GitHub CLI command to execute (without 'gh' prefix)

**Examples:**

```bash
# Repository operations
github_cli command="repo list"
github_cli command="repo create my-new-repo --public --description 'My awesome project'"
github_cli command="repo view octocat/Hello-World"
github_cli command="repo clone octocat/Hello-World"

# Issue operations
github_cli command="issue list --repo octocat/Hello-World"
github_cli command="issue create --repo octocat/Hello-World --title 'Found a bug' --body 'Description of the bug'"
github_cli command="issue view 123 --repo octocat/Hello-World"
github_cli command="issue close 123 --repo octocat/Hello-World"

# Pull request operations
github_cli command="pr list --repo octocat/Hello-World"
github_cli command="pr create --repo octocat/Hello-World --title 'Fix bug' --body 'This fixes the bug'"
github_cli command="pr view 456 --repo octocat/Hello-World"
github_cli command="pr merge 456 --repo octocat/Hello-World"

# Organization operations
github_cli command="org list"
github_cli command="repo list --org my-organization"

# User operations
github_cli command="api user"
github_cli command="auth status"

# Advanced operations with JSON output
github_cli command="repo list --json name,description,visibility,language,stargazerCount"
github_cli command="issue list --repo octocat/Hello-World --json number,title,state,author,createdAt"
```

## Common Use Cases

### Repository Management
```bash
# List repositories
github_cli command="repo list"

# Create a new repository
github_cli command="repo create my-project --public --add-readme --gitignore Python --license MIT"

# Get repository information
github_cli command="repo view owner/repo"

# Clone a repository
github_cli command="repo clone owner/repo"
```

### Issue Management
```bash
# List issues
github_cli command="issue list --repo owner/repo --state open"

# Create an issue
github_cli command="issue create --repo owner/repo --title 'Bug Report' --body 'Description' --label bug"

# View an issue
github_cli command="issue view 123 --repo owner/repo"

# Close an issue
github_cli command="issue close 123 --repo owner/repo"
```

### Pull Request Management
```bash
# List pull requests
github_cli command="pr list --repo owner/repo --state open"

# Create a pull request
github_cli command="pr create --repo owner/repo --title 'Feature' --body 'Description' --head feature-branch"

# View a pull request
github_cli command="pr view 456 --repo owner/repo"

# Merge a pull request
github_cli command="pr merge 456 --repo owner/repo"
```

### Advanced Operations
```bash
# Get JSON output for parsing
github_cli command="repo list --json name,description,visibility,language,stargazerCount,forkCount"

# Search repositories
github_cli command="search repos --owner octocat"

# API calls
github_cli command="api /user/repos"

# Authentication
github_cli command="auth status"
```

## Environment Variables

The following environment variables are required:

- `GITHUB_TOKEN`: GitHub personal access token with appropriate permissions

Optional environment variables:
- `GITHUB_REPOSITORY`: Default repository for operations
- `GITHUB_ORGANIZATION`: Default organization for operations

## Authentication

To use this tool, you need to set up GitHub authentication:

1. Generate a GitHub personal access token with the required permissions:
   - `repo` - Full control of private repositories
   - `public_repo` - Access to public repositories
   - `read:org` - Read organization membership
   - `user` - Read user profile data

2. Set the token as the `GITHUB_TOKEN` environment variable

## Installation

```bash
pip install -r requirements.txt
pip install -e .
```

## Docker Usage

```bash
# Build the Docker image
docker build -t github-cli-tools .

# Run with environment variables
docker run -e GITHUB_TOKEN=your_token github-cli-tools
```

## Error Handling

The tool includes comprehensive error handling:
- Environment variable validation
- Command argument validation
- GitHub CLI error responses
- Network connectivity issues
- Exit code propagation

## AI Usage Tips

When using this tool with AI:

1. **Pass complete commands**: Include all necessary flags and arguments
2. **Use proper quoting**: Quote strings with spaces: `--title "My Title"`
3. **Specify repositories**: Use `--repo owner/repo` format when needed
4. **Use JSON output**: Add `--json` flag for structured data when parsing is needed
5. **Check GitHub CLI docs**: The tool supports all official `gh` commands

## Supported Commands

This tool supports all GitHub CLI commands including:
- `repo` - Repository operations
- `issue` - Issue management
- `pr` - Pull request operations
- `org` - Organization management
- `user` - User operations
- `auth` - Authentication
- `api` - Direct API calls
- `search` - Search operations
- `workflow` - GitHub Actions workflows
- `release` - Release management
- And many more...

## Security Notes

- Store your GitHub token securely
- Use environment variables, not hardcoded values
- Follow the principle of least privilege when generating tokens
- Regularly rotate your access tokens
- Be careful with destructive operations

## Support

For issues, questions, or contributions, please refer to the Kubiya documentation or contact the development team.

For GitHub CLI specific help, run:
```bash
github_cli command="help"
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 