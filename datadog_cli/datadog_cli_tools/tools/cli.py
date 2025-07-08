import sys
import os
from .base import DatadogCLITool, Arg, FileSpec
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
        
        # Create the .dogrc configuration file content
        dogrc_content = """[Connection]
apikey = ${DD_API_KEY}
appkey = ${DD_APP_KEY}
api_host = https://api.${DD_SITE}
"""
        
        # Write the .dogrc file to a temporary location
        dogrc_path = "/tmp/.dogrc"
        with open(dogrc_path, "w") as f:
            f.write(dogrc_content)
        
        # Define file specifications
        file_specs = [
            FileSpec(
                source=dogrc_path,
                destination="/root/.dogrc"
            )
        ]
        
        return DatadogCLITool(
            name="datadog_cli_command",
            description="Execute any Datadog CLI command with full functionality using Dogshell",
            content="""
            set -e  # Exit on any error
            
            # Install datadog package if not already installed
            echo "Installing datadog package..."
            pip install datadog --quiet --no-cache-dir
            echo "✅ Datadog package installed successfully"
            
            # Validate required parameters
            if [ -z "$command" ]; then
                echo "❌ Error: Command is required"
                echo ""
                echo "Usage: Provide a Dogshell command (e.g., 'monitor list', 'dashboard list')"
                echo ""
                echo "Common commands:"
                echo "  • monitor list          - List all monitors"
                echo "  • dashboard list        - List all dashboards"
                echo "  • metric post           - Post a metric"
                echo "  • event post            - Post an event"
                echo "  • host list             - List hosts"
                echo "  • tag list              - List tags"
                echo "  • search                - Search metrics/events"
                echo "  • comment post          - Post a comment"
                exit 1
            fi
            
            # Validate authentication environment variables
            if [ -z "$DD_API_KEY" ]; then
                echo "❌ Error: DD_API_KEY environment variable is not set"
                echo ""
                echo "💡 Hint: Set your Datadog API key:"
                echo "  export DD_API_KEY='your-api-key-here'"
                echo ""
                echo "You can find your API key in Datadog:"
                echo "  Settings → API Keys → Create API Key"
                exit 1
            fi
            
            if [ -z "$DD_APP_KEY" ]; then
                echo "❌ Error: DD_APP_KEY environment variable is not set"
                echo ""
                echo "💡 Hint: Set your Datadog Application key:"
                echo "  export DD_APP_KEY='your-app-key-here'"
                echo ""
                echo "You can find your Application key in Datadog:"
                echo "  Settings → Application Keys → Create Application Key"
                exit 1
            fi
            
            if [ -z "$DD_SITE" ]; then
                echo "❌ Error: DD_SITE environment variable is not set"
                echo ""
                echo "💡 Hint: Set your Datadog site:"
                echo "  export DD_SITE='datadoghq.com'  # US site"
                echo "  export DD_SITE='datadoghq.eu'   # EU site"
                echo "  export DD_SITE='us3.datadoghq.com'  # US3 site"
                exit 1
            fi
            
            echo "=== Executing Datadog Command with Dogshell ==="
            echo "Command: python -m datadog.dog $command"
            echo "Site: $DD_SITE"
            echo "Timestamp: $(date)"
            echo ""
            
            # Execute the dog command using Python module
            echo "Executing command..."
            output=$(python -m datadog.dog $command 2>&1)
            exit_code=$?
            
            echo "Command completed with exit code: $exit_code"
            
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
                if echo "$output" | grep -q "command not found\|unknown command\|No module named\|usage:"; then
                    echo "💡 Hint: The command '$command' is not recognized."
                    echo ""
                    echo "Common dog commands:"
                    echo "  • python -m datadog.dog monitor list"
                    echo "  • python -m datadog.dog dashboard list"
                    echo "  • python -m datadog.dog metric post"
                    echo "  • python -m datadog.dog event post"
                    echo "  • python -m datadog.dog host list"
                    echo "  • python -m datadog.dog tag list"
                    echo "  • python -m datadog.dog search"
                    echo "  • python -m datadog.dog comment post"
                    echo ""
                    echo "💡 Tip: Use 'python -m datadog.dog -h' to see all available commands"
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
                    echo "  • Use 'python -m datadog.dog $command -h' for usage information"
                    echo "  • Verify required parameters are provided"
                else
                    echo "💡 General troubleshooting tips:"
                    echo "  • Use 'python -m datadog.dog -h' to see available commands"
                    echo "  • Use 'python -m datadog.dog $command -h' for specific command help"
                    echo "  • Check Dogshell documentation: https://docs.datadoghq.com/developers/guide/dogshell/"
                    echo "  • Verify your Datadog account permissions"
                fi
                
                exit $exit_code
            fi
            """,
            args=[
                Arg(name="command", description="The command to pass to dog (e.g., 'monitor list', 'metric post', 'event post')", required=True)
            ],
            image="python:3.9-slim",
            with_files=file_specs
        )

CLITools() 