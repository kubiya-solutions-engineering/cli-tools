# Confluence Search Tools

A Confluence search tool for Kubiya, providing AI-controlled access to search across Confluence spaces and pages.

## Overview

This package provides a tool that integrates with Confluence's REST API to search through Confluence spaces and pages, allowing AI agents to find relevant documentation and content based on search queries.

## Features

- **Confluence Search**: Search through Confluence spaces using natural language queries
- **Space-Specific Search**: Optionally limit searches to specific Confluence spaces
- **Rich Results**: Returns page titles, excerpts, URLs, and space information
- **Flexible Queries**: Supports any search terms that work with Confluence's search
- **AI-Friendly**: Designed for AI agents to easily find and reference documentation
- **Authenticated**: Secure API token-based authentication

## Available Tools

### `confluence_search`
Search through Confluence spaces using a search query. You can search across all spaces or limit to a specific space.

**Parameters:**
- `query` (required): The search query to find relevant pages
- `space_key` (optional): Confluence space key to limit search to a specific space
- `limit` (optional): Maximum number of results to return (default: 10)

**Examples:**

```bash
# Search across all spaces
confluence_search query="API documentation"

# Search in a specific space
confluence_search query="user authentication" space_key="DEV"

# Search with custom result limit
confluence_search query="troubleshooting guide" limit="20"

# Search for specific topics
confluence_search query="deployment process"
confluence_search query="database schema" space_key="DOCS"
confluence_search query="security guidelines" limit="5"
```

## Authentication Setup

The tool requires three environment variables for authentication:

1. **CONFLUENCE_URL**: Your Confluence instance URL (e.g., `https://yourcompany.atlassian.net/wiki`)
2. **CONFLUENCE_USERNAME**: Your Confluence username/email
3. **CONFLUENCE_API_TOKEN**: Your Confluence API token

### Getting Your API Token

1. Go to your Atlassian Account Settings: https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a label (e.g., "Kubiya Integration")
4. Copy the generated token

### Environment Variables

Set these environment variables in your Kubiya configuration:

```bash
export CONFLUENCE_URL="https://yourcompany.atlassian.net/wiki"
export CONFLUENCE_USERNAME="your-email@company.com" 
export CONFLUENCE_API_TOKEN="your-api-token-here"
```

## Installation

1. Ensure you have the required environment variables set up
2. Install the package dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install the package:
   ```bash
   pip install -e .
   ```

## Usage Examples

### Basic Search
```bash
confluence_search query="onboarding process"
```

### Search in Development Space
```bash
confluence_search query="API endpoints" space_key="DEV"
```

### Search with More Results
```bash
confluence_search query="troubleshooting" limit="15"
```

### Complex Queries
```bash
confluence_search query="user management AND permissions"
confluence_search query="deployment OR release process"
confluence_search query="database migration"
```

## Search Results

The tool returns structured results with:
- **Title**: Page or content title
- **Space**: The Confluence space containing the content
- **Type**: Content type (usually "page")
- **URL**: Direct link to the content
- **Excerpt**: Brief preview of the content (when available)

Example output:
```
🔍 Searching Confluence for: 'API documentation'
🔗 URL: https://yourcompany.atlassian.net/wiki
============================================================

📊 Found 3 result(s):

🔸 Result #1
   📄 Title: REST API Reference
   🏠 Space: Developer Documentation
   📋 Type: page
   🔗 URL: https://yourcompany.atlassian.net/wiki/display/DEV/REST+API+Reference
   📝 Excerpt: Complete reference for all REST API endpoints including authentication...

🔸 Result #2
   📄 Title: API Authentication Guide
   🏠 Space: Developer Documentation
   📋 Type: page
   🔗 URL: https://yourcompany.atlassian.net/wiki/display/DEV/API+Authentication+Guide
   📝 Excerpt: Learn how to authenticate with our APIs using OAuth 2.0 and API keys...

============================================================
✅ Search completed successfully. Found 3 result(s).
```

## Error Handling

The tool provides clear error messages for common issues:
- Missing or invalid credentials
- Network connectivity problems
- Invalid Confluence URLs
- Empty search results
- API rate limiting

## Requirements

- Python 3.8+
- `requests` library for HTTP requests
- `beautifulsoup4` for HTML parsing
- `kubiya-sdk` for Kubiya integration
- Valid Confluence instance with API access

## Troubleshooting

### Authentication Issues
- Verify your Confluence URL is correct and includes `/wiki` if using Atlassian Cloud
- Ensure your API token is valid and not expired
- Check that your username/email is correct

### No Results Found
- Try broader search terms
- Check if the space key exists (if specified)
- Verify you have access to the content you're searching for

### Connection Issues
- Confirm your Confluence instance is accessible
- Check network connectivity
- Verify firewall/proxy settings if applicable

## Development

To extend or modify the tool:

1. The main search logic is in `confluence_tools/tools/search.py`
2. Base tool functionality is in `confluence_tools/tools/base.py`
3. Add new tools by extending the `ConfluenceTool` class

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License. 