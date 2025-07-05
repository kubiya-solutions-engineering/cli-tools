from typing import List
import sys
from .base import DatadogCLITool, Arg
from kubiya_sdk.tools.registry import tool_registry

class CLITools:
    """Datadog CLI wrapper tools."""

    def __init__(self):
        """Initialize and register all Datadog CLI tools."""
        try:
            tools = [
                self.run_cli_command()
            ]
            
            for tool in tools:
                try:
                    tool_registry.register("datadog_cli", tool)
                    print(f"✅ Registered: {tool.name}")
                except Exception as e:
                    print(f"❌ Failed to register {tool.name}: {str(e)}", file=sys.stderr)
                    raise
        except Exception as e:
            print(f"❌ Failed to register Datadog CLI tools: {str(e)}", file=sys.stderr)
            raise

    def run_cli_command(self) -> DatadogCLITool:
        """Execute a Datadog CLI command."""
        return DatadogCLITool(
            name="datadog_cli_command",
            description="Execute any Datadog CLI command",
            content="""
            # Validate required parameters
            if [ -z "$command" ]; then
                echo "Error: Command is required"
                exit 1
            fi
            
            echo "=== Executing Datadog CLI Command ==="
            echo "Command: datadog $command"
            echo ""
            
            # Execute the command
            datadog $command
            """,
            args=[
                Arg(name="command", description="The command to pass to the Datadog CLI (e.g., 'monitor list', 'dashboards list')", required=True)
            ],
            image="datadog/cli:latest"
        )

CLITools() 