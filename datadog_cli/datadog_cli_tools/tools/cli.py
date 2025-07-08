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
        """Execute any Datadog CLI command."""
        return DatadogCLITool(
            name="datadog_cli_command",
            description="Execute any Datadog CLI command with full functionality",
            content="""
            # Validate required parameters
            if [ -z "$command" ]; then
                echo "Error: Command is required"
                echo "Usage: Provide a Datadog CLI command (e.g., 'monitor list', 'dashboard list')"
                exit 1
            fi
            
            # Validate authentication environment variables
            if [ -z "$DD_API_KEY" ]; then
                echo "❌ Error: DD_API_KEY environment variable is not set"
                echo "Please configure your Datadog API key"
                exit 1
            fi
            
            if [ -z "$DD_APP_KEY" ]; then
                echo "❌ Error: DD_APP_KEY environment variable is not set"
                echo "Please configure your Datadog Application key"
                exit 1
            fi
            
            if [ -z "$DD_SITE" ]; then
                echo "❌ Error: DD_SITE environment variable is not set"
                echo "Please configure your Datadog site"
                exit 1
            fi
            
            echo "=== Executing Datadog CLI Command ==="
            echo "Command: datadog $command"
            echo "Site: $DD_SITE"
            echo "Timestamp: $(date)"
            echo ""
            
            # Execute the command with error handling
            if datadog $command; then
                echo ""
                echo "✅ Command executed successfully"
            else
                echo ""
                echo "❌ Command failed with exit code $?"
                exit 1
            fi
            """,
            args=[
                Arg(name="command", description="The command to pass to the Datadog CLI (e.g., 'monitor list', 'dashboards list', 'logs list')", required=True)
            ],
            image="datadog/cli:latest"
        )

CLITools() 