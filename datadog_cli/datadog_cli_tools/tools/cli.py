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
            description="Execute any Datadog CLI command with full functionality using Dogshell",
            content="""
            set -e  # Exit on any error
            
            # Install datadog package if not already installed
            echo "Installing datadog package..."
            pip install datadog --quiet --no-cache-dir
            echo "✅ Datadog package installed successfully"
            
            # Ensure dog command is available
            echo "Checking for dog command..."
            if command -v dog &> /dev/null; then
                echo "✅ dog command is available at: $(which dog)"
            else
                echo "❌ dog command not found, attempting to locate it..."
                
                # Check common locations for dog command
                DOG_FOUND=""
                
                # Check /usr/local/bin/dog
                if [ -f "/usr/local/bin/dog" ] && [ -x "/usr/local/bin/dog" ]; then
                    DOG_FOUND="/usr/local/bin/dog"
                    echo "✅ Found dog command at: /usr/local/bin/dog"
                fi
                
                # Check alongside python executable
                if [ -z "$DOG_FOUND" ]; then
                    PYTHON_DIR="$(dirname $(which python))"
                    if [ -f "$PYTHON_DIR/dog" ] && [ -x "$PYTHON_DIR/dog" ]; then
                        DOG_FOUND="$PYTHON_DIR/dog"
                        echo "✅ Found dog command at: $PYTHON_DIR/dog"
                    fi
                fi
                
                # Check python executable replacement
                if [ -z "$DOG_FOUND" ]; then
                    PYTHON_DOG_PATH="$(python -c 'import sys; print(sys.executable.replace("python", "dog"))' 2>/dev/null)"
                    if [ -f "$PYTHON_DOG_PATH" ] && [ -x "$PYTHON_DOG_PATH" ]; then
                        DOG_FOUND="$PYTHON_DOG_PATH"
                        echo "✅ Found dog command at: $PYTHON_DOG_PATH"
                    fi
                fi
                
                if [ -z "$DOG_FOUND" ]; then
                    echo "❌ Error: Could not locate dog command"
                    echo ""
                    echo "💡 Debugging info:"
                    echo "  • Python location: $(which python)"
                    echo "  • Datadog package: $(python -c 'import datadog; print(datadog.__file__)' 2>/dev/null || echo 'Not found')"
                    echo "  • PATH: $PATH"
                    echo ""
                    echo "💡 Try: pip install datadog --upgrade --force-reinstall"
                    exit 1
                fi
                
                # Add dog directory to PATH
                DOG_DIR="$(dirname "$DOG_FOUND")"
                export PATH="$DOG_DIR:$PATH"
                echo "✅ Added $DOG_DIR to PATH"
            fi
            
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
            
            echo "=== Executing Datadog Command with Dogshell ==="
            echo "Command: dog $command"
            echo "Timestamp: $(date)"
            echo ""
            
            # Execute the dog command directly
            echo "Executing command..."
            
            # Execute the dog command (we've already verified it's available)
            echo "Running: dog $command"
            output=$(dog $command 2>&1)
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
                
                # Get available commands from dog -h for better error guidance
                echo "📋 Getting available commands to help troubleshoot..."
                help_output=""
                if command -v dog &> /dev/null; then
                    help_output=$(dog -h 2>&1 || echo "Failed to get help")
                elif python -c "import datadog.dogshell" &> /dev/null; then
                    help_output=$(python -m datadog.dogshell -h 2>&1 || echo "Failed to get help")
                else
                    help_output="Help not available - dogshell not found"
                fi
                
                echo ""
                echo "=== Available Datadog Commands ==="
                echo "$help_output"
                echo ""
                echo "=== Troubleshooting Guide ==="
                
                # Provide helpful hints based on common error patterns
                if echo "$output" | grep -q "command not found\|unknown command\|No module named\|usage:\|invalid choice"; then
                    echo "💡 Hint: The command '$command' is not recognized."
                    echo ""
                    echo "Common dog commands:"
                    echo "  • dog monitor list"
                    echo "  • dog dashboard list"
                    echo "  • dog metric post"
                    echo "  • dog event post"
                    echo "  • dog host list"
                    echo "  • dog tag list"
                    echo "  • dog search"
                    echo "  • dog comment post"
                    echo ""
                    echo "💡 Tip: Check the available commands above and try again"
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
                    echo "  • Use 'dog $command -h' for usage information"
                    echo "  • Verify required parameters are provided"
                elif echo "$output" | grep -q "required\|missing"; then
                    echo "💡 Hint: Missing required parameters."
                    echo "  • Check the command syntax above"
                    echo "  • Use 'dog $command -h' for specific parameter requirements"
                    echo "  • Ensure all required arguments are provided"
                else
                    echo "💡 General troubleshooting tips:"
                    echo "  • Use 'dog -h' to see available commands"
                    echo "  • Use 'dog $command -h' for specific command help"
                    echo "  • Check Dogshell documentation: https://docs.datadoghq.com/developers/guide/dogshell/"
                    echo "  • Verify your Datadog account permissions"
                fi
                
                echo ""
                echo "💡 Quick Actions:"
                echo "  • Run 'dog -h' to see all available commands"
                echo "  • Run 'dog $command -h' to see specific command usage"
                echo "  • Check your environment variables (DD_API_KEY, DD_APP_KEY, DD_SITE)"
                
                exit $exit_code
            fi
            """,
            args=[
                Arg(name="command", description="The command to pass to dog (e.g., 'monitor list', 'metric post', 'event post')", required=True)
            ],
            image="python:3.9-slim"
        )

CLITools() 