from typing import List
import sys
from .base import ConfluenceTool, Arg
from kubiya_sdk.tools.registry import tool_registry

class ConfluenceSearchTools:
    """Confluence search tools for AI-controlled Confluence operations."""

    def __init__(self):
        """Initialize and register the Confluence search tools."""
        try:
            # Register the main Confluence search tool
            search_tool = self.confluence_search()
            tool_registry.register("confluence_search", search_tool)
            print(f"✅ Registered: {search_tool.name}")
        except Exception as e:
            print(f"❌ Failed to register Confluence search tools: {str(e)}", file=sys.stderr)
            raise

    def confluence_search(self) -> ConfluenceTool:
        """Search through Confluence spaces based on a search query."""
        return ConfluenceTool(
            name="confluence_search",
            description="Search through Confluence spaces using a search query. Provide a search query and optionally specify a space key to limit the search to a specific space. Returns matching pages with titles, excerpts, and URLs.",
            content="""
            # Install required packages
            pip install requests beautifulsoup4 --quiet
            
            # Create the Python search script
            cat > /tmp/confluence_search.py << 'EOF'
import os
import sys
import requests
import json
from urllib.parse import quote
from bs4 import BeautifulSoup

def search_confluence():
    # Validate environment variables
    confluence_url = os.getenv('CONFLUENCE_URL')
    username = os.getenv('CONFLUENCE_USERNAME')
    api_token = os.getenv('CONFLUENCE_API_TOKEN')
    
    if not confluence_url:
        print("❌ CONFLUENCE_URL environment variable is required")
        sys.exit(1)
    
    if not username:
        print("❌ CONFLUENCE_USERNAME environment variable is required")
        sys.exit(1)
    
    if not api_token:
        print("❌ CONFLUENCE_API_TOKEN environment variable is required")
        sys.exit(1)
    
    # Get parameters
    query = os.getenv('query')
    space_key = os.getenv('space_key', '')  # Optional
    limit = int(os.getenv('limit', '10'))
    
    if not query:
        print("❌ Search query is required")
        print("Usage: Provide a search query to find relevant pages in Confluence")
        print("Examples:")
        print("  query='API documentation'")
        print("  query='user authentication' space_key='DEV'")
        print("  query='troubleshooting guide' limit='20'")
        sys.exit(1)
    
    # Clean up URL (remove trailing slash)
    confluence_url = confluence_url.rstrip('/')
    
    # Build search URL
    search_url = f"{confluence_url}/rest/api/search"
    
    # Build CQL (Confluence Query Language) query
    cql_query = f'text ~ "{query}"'
    if space_key:
        cql_query += f' and space = "{space_key}"'
    
    # Parameters for the search
    params = {
        'cql': cql_query,
        'limit': limit,
        'expand': 'content.space,content.version,content.body.view'
    }
    
    print(f"🔍 Searching Confluence for: '{query}'")
    if space_key:
        print(f"📁 In space: {space_key}")
    print(f"🔗 URL: {confluence_url}")
    print("=" * 60)
    
    try:
        # Make the API request
        response = requests.get(
            search_url,
            params=params,
            auth=(username, api_token),
            headers={'Accept': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 401:
            print("❌ Authentication failed. Please check your credentials.")
            sys.exit(1)
        elif response.status_code == 404:
            print("❌ Confluence instance not found. Please check the URL.")
            sys.exit(1)
        elif response.status_code != 200:
            print(f"❌ API request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            sys.exit(1)
        
        data = response.json()
        results = data.get('results', [])
        
        if not results:
            print("📭 No results found for your search query.")
            return
        
        print(f"📊 Found {len(results)} result(s):")
        print()
        
        for i, result in enumerate(results, 1):
            content = result.get('content', {})
            title = content.get('title', 'No title')
            space_name = content.get('space', {}).get('name', 'Unknown space')
            content_type = content.get('type', 'page')
            
            # Build the page URL
            page_url = f"{confluence_url}/display/{content.get('space', {}).get('key', '')}/{content.get('title', '').replace(' ', '+')}"
            
            print(f"🔸 Result #{i}")
            print(f"   📄 Title: {title}")
            print(f"   🏠 Space: {space_name}")
            print(f"   📋 Type: {content_type}")
            print(f"   🔗 URL: {page_url}")
            
            # Get excerpt if available
            excerpt = result.get('excerpt', '')
            if excerpt:
                # Clean HTML from excerpt
                soup = BeautifulSoup(excerpt, 'html.parser')
                clean_excerpt = soup.get_text().strip()
                if clean_excerpt:
                    print(f"   📝 Excerpt: {clean_excerpt[:200]}{'...' if len(clean_excerpt) > 200 else ''}")
            
            print()
        
        print("=" * 60)
        print(f"✅ Search completed successfully. Found {len(results)} result(s).")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    search_confluence()
EOF

            # Run the search script
            python /tmp/confluence_search.py
            """,
            args=[
                Arg(name="query", description="The search query to find relevant pages in Confluence. Examples: 'API documentation', 'user authentication', 'troubleshooting guide'", required=True),
                Arg(name="space_key", description="Optional: Confluence space key to limit search to a specific space (e.g., 'DEV', 'DOCS')", required=False),
                Arg(name="limit", description="Optional: Maximum number of results to return (default: 10)", required=False)
            ]
        )


# Initialize the search tools when the module is imported
confluence_search_tools = ConfluenceSearchTools() 