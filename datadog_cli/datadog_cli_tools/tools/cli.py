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
            
            # Capture command output and error
            output=$(datadog $command 2>&1)
            exit_code=$?
            
            if [ $exit_code -eq 0 ]; then
                echo "$output"
                echo ""
                echo "✅ Command executed successfully"
            else
                echo "❌ Command failed with exit code $exit_code"
                echo ""
                echo "Command output:"
                echo "$output"
                echo ""
                
                # Provide helpful hints based on common error patterns
                if echo "$output" | grep -q "command not found\|unknown command"; then
                    echo "💡 Hint: The command '$command' is not recognized."
                    echo ""
                    echo "Common Datadog CLI commands:"
                    echo "  • datadog monitor list"
                    echo "  • datadog dashboard list"
                    echo "  • datadog logs list"
                    echo "  • datadog service list"
                    echo "  • datadog host list"
                    echo "  • datadog metric list"
                    echo "  • datadog user list"
                    echo "  • datadog org list"
                    echo ""
                    echo "💡 Tip: Use 'datadog --help' to see all available commands"
                elif echo "$output" | grep -q "authentication\|unauthorized\|403\|401"; then
                    echo "💡 Hint: Authentication failed. Please check:"
                    echo "  • DD_API_KEY is correct and has proper permissions"
                    echo "  • DD_APP_KEY is correct and has proper permissions"
                    echo "  • DD_SITE is set to the correct Datadog site"
                    echo ""
                    echo "💡 Tip: Verify your API key permissions in Datadog:"
                    echo "  Settings → API Keys → Check permissions"
                elif echo "$output" | grep -q "not found\|404"; then
                    echo "💡 Hint: The requested resource was not found."
                    echo "  • Check if the resource ID/name is correct"
                    echo "  • Verify the resource exists in your Datadog account"
                    echo "  • Ensure you have access to the resource"
                elif echo "$output" | grep -q "rate limit\|429"; then
                    echo "💡 Hint: Rate limit exceeded."
                    echo "  • Wait a moment and try again"
                    echo "  • Consider using pagination for large datasets"
                    echo "  • Check your Datadog plan limits"
                elif echo "$output" | grep -q "invalid\|syntax\|malformed"; then
                    echo "💡 Hint: Invalid command syntax."
                    echo "  • Check command spelling and format"
                    echo "  • Use 'datadog $command --help' for usage information"
                    echo "  • Verify required parameters are provided"
                else
                    echo "💡 General troubleshooting tips:"
                    echo "  • Use 'datadog --help' to see available commands"
                    echo "  • Use 'datadog $command --help' for specific command help"
                    echo "  • Check Datadog documentation: https://docs.datadoghq.com/cli/"
                    echo "  • Verify your Datadog account permissions"
                fi
                
                exit $exit_code
            fi
            """,
            args=[
                Arg(name="command", description="The command to pass to the Datadog CLI (e.g., 'monitor list', 'dashboards list', 'logs list')", required=True)
            ],
            image="datadog/cli:latest"
        )

CLITools() 