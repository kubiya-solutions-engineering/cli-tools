from typing import List
import sys
from .base import HelmCLITool, Arg
from kubiya_sdk.tools.registry import tool_registry

class CLITools:
    """Helm CLI wrapper tools."""

    def __init__(self):
        """Initialize and register all Helm CLI tools."""
        try:
            tools = [
                self.run_cli_command()
            ]
            
            for tool in tools:
                try:
                    tool_registry.register("helm_cli", tool)
                    print(f"✅ Registered: {tool.name}")
                except Exception as e:
                    print(f"❌ Failed to register {tool.name}: {str(e)}", file=sys.stderr)
                    raise
        except Exception as e:
            print(f"❌ Failed to register Helm CLI tools: {str(e)}", file=sys.stderr)
            raise

    def run_cli_command(self) -> HelmCLITool:
        """Execute a Helm CLI command."""
        return HelmCLITool(
            name="helm_cli_command",
            description="Execute any Helm CLI command",
            content="""
            # Validate required parameters
            if [ -z "$command" ]; then
                echo "Error: Command is required"
                exit 1
            fi
            
            echo "=== Executing Helm CLI Command ==="
            echo "Command: helm $command"
            echo ""
            
            # Execute the command
            helm $command
            """,
            args=[
                Arg(name="command", description="The command to pass to the Helm CLI (e.g., 'list', 'install my-release ./chart', 'upgrade my-release ./chart')", required=True)
            ],
            image="alpine/helm:latest"
        )

CLITools() 