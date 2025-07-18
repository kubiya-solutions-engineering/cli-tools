from typing import List
import sys
from .base import GitHubCLITool, Arg
from kubiya_sdk.tools.registry import tool_registry

class CLITools:
    """GitHub CLI wrapper tool for AI-controlled GitHub operations."""

    def __init__(self):
        """Initialize and register the GitHub CLI tool."""
        try:
            tool = self.github_cli()
            tool_registry.register("github_cli", tool)
            print(f"✅ Registered: {tool.name}")
        except Exception as e:
            print(f"❌ Failed to register GitHub CLI tool: {str(e)}", file=sys.stderr)
            raise

    def github_cli(self) -> GitHubCLITool:
        """A flexible GitHub CLI wrapper that allows AI to execute any gh command."""
        return GitHubCLITool(
            name="github_cli",
            description="Execute GitHub CLI commands. Pass any 'gh' command as the 'command' argument. The tool will handle authentication and execute the command, returning the output. Examples: 'repo list', 'issue create --title \"Bug\" --body \"Description\"', 'pr list --state open', etc.",
            content="""
            # Validate environment
            if [ -z "$GH_TOKEN" ]; then
                echo "❌ GH_TOKEN environment variable is required"
                exit 1
            fi
            
            if [ -z "$command" ]; then
                echo "❌ Command argument is required"
                echo "Usage: Pass any 'gh' command as the 'command' argument"
                echo "Examples:"
                echo "  command='repo list'"
                echo "  command='issue create --title \"Bug\" --body \"Description\"'"
                echo "  command='pr list --state open'"
                exit 1
            fi
            
            # Install required packages
            apk add --no-cache jq curl github-cli git >/dev/null 2>&1 || {
                echo "❌ Failed to install required packages"
                exit 1
            }
            
            # Set up GitHub CLI authentication
            export GH_TOKEN="$GH_TOKEN"
            
            # Parse the command
            cmd="$command"
            
            echo "🔧 Executing GitHub CLI command: gh $cmd"
            echo "----------------------------------------"
            
            # Execute the gh command
            eval "gh $cmd"
            
            exit_code=$?
            
            if [ $exit_code -eq 0 ]; then
                echo "----------------------------------------"
                echo "✅ Command executed successfully"
            else
                echo "----------------------------------------"
                echo "❌ Command failed with exit code: $exit_code"
                exit $exit_code
            fi
            """,
            args=[
                Arg(name="command", description="The GitHub CLI command to execute (without 'gh' prefix). Examples: 'repo list', 'issue create --title \"Bug\"', 'pr list --state open'", required=True)
            ]
        )


# Initialize the CLI tools when the module is imported
cli_tools = CLITools() 