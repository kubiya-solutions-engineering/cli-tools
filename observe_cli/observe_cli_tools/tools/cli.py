from typing import List
import sys
from .base import ObserveCLITool, Arg
from kubiya_sdk.tools.registry import tool_registry

class CLITools:
    """Observe CLI wrapper tools."""

    def __init__(self):
        """Initialize and register all Observe CLI tools."""
        try:
            tools = [
                self.run_cli_command()
            ]
            
            for tool in tools:
                try:
                    tool_registry.register("observe_cli", tool)
                    print(f"✅ Registered: {tool.name}")
                except Exception as e:
                    print(f"❌ Failed to register {tool.name}: {str(e)}", file=sys.stderr)
                    raise
        except Exception as e:
            print(f"❌ Failed to register Observe CLI tools: {str(e)}", file=sys.stderr)
            raise

    def run_cli_command(self) -> ObserveCLITool:
        """Execute an Observe CLI command."""
        return ObserveCLITool(
            name="observe_cli_command",
            description="Execute any Observe CLI command",
            content="""
            # Install observe CLI if not present
            if ! command -v observe &> /dev/null; then
                echo "Installing Observe CLI..."
                curl -L https://github.com/observeinc/cli/releases/latest/download/observe-cli-linux-amd64 -o /usr/local/bin/observe
                chmod +x /usr/local/bin/observe
            fi
            
            # Validate required parameters
            if [ -z "$command" ]; then
                echo "Error: Command is required"
                exit 1
            fi
            
            echo "=== Executing Observe CLI Command ==="
            echo "Command: observe $command"
            echo ""
            
            # Execute the command
            /usr/local/bin/observe $command
            """,
            args=[
                Arg(name="command", description="The command to pass to the Observe CLI (e.g., 'datasets list', 'monitors list')", required=True)
            ],
            image="alpine:latest"
        )

CLITools() 