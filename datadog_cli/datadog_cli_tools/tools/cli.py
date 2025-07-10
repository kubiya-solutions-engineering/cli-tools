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
            cat /root/.dogrc
            
            # Install datadog package if not already installed
            echo "Installing datadog package..."
            pip install datadog --quiet --no-cache-dir
            echo "✅ Datadog package installed successfully"
            echo ""
            
            # Validate required parameters first
            if [ -z "$command" ]; then
                echo "❌ Error: Command is required"
                echo ""
                echo "Usage: Provide a Dogshell command (e.g., 'monitor show_all', 'dashboard list')"
                echo ""
                echo "Common commands:"
                echo "  • monitor show_all      - Show all monitors"
                echo "  • monitor show <id>     - Show specific monitor"
                echo "  • dashboard list        - List all dashboards"
                echo "  • metric post           - Post a metric"
                echo "  • event post            - Post an event"
                echo "  • host list             - List hosts"
                echo "  • tag list              - List tags"
                echo "  • search                - Search metrics/events"
                echo "  • comment post          - Post a comment"
                exit 1
            fi
            
            # Find the dog command
            echo "Locating dog command..."
            DOG_CMD=""
            
            # Check if dog is in PATH
            if command -v dog &> /dev/null; then
                DOG_CMD="dog"
                echo "✅ Found dog command in PATH"
            else
                # Try to find dog in common locations
                PYTHON_DIR="$(dirname $(which python))"
                if [ -f "$PYTHON_DIR/dog" ] && [ -x "$PYTHON_DIR/dog" ]; then
                    DOG_CMD="$PYTHON_DIR/dog"
                    echo "✅ Found dog command at: $PYTHON_DIR/dog"
                else
                    # Try using python module directly
                    if python -c "import datadog.dogshell" &> /dev/null; then
                        DOG_CMD="python -m datadog.dogshell"
                        echo "✅ Using python module: datadog.dogshell"
                    else
                        echo "❌ Error: Could not locate dog command or datadog.dogshell module"
                        exit 1
                    fi
                fi
            fi
            
            echo "=== Executing Datadog Command ==="
            echo "Command: $DOG_CMD $command"
            echo "Timestamp: $(date)"
            echo ""
            
            # Execute the command with timeout and proper output handling
            echo "Executing command..."
            
            # Use a more reliable execution method
            set +e  # Don't exit on error so we can handle it
            
            # Execute with timeout and capture output
            timeout 60 $DOG_CMD $command 2>&1
            exit_code=$?
            
            # Handle the results
            if [ $exit_code -eq 124 ]; then
                echo ""
                echo "❌ Command timed out after 60 seconds"
                echo ""
                echo "💡 This might indicate:"
                echo "  • Authentication issues (check DD_API_KEY, DD_APP_KEY)"
                echo "  • Network connectivity problems"
                echo "  • Invalid command syntax"
                echo "  • Datadog API is slow to respond"
                exit 1
            elif [ $exit_code -eq 0 ]; then
                echo ""
                echo "✅ Command executed successfully"
            else
                echo ""
                echo "❌ Command failed with exit code $exit_code"
                echo ""
                echo "💡 Troubleshooting tips:"
                
                # Provide specific help based on common issues
                if [ $exit_code -eq 1 ]; then
                    echo "  • Check command syntax: $DOG_CMD $command"
                    echo "  • Verify authentication credentials"
                    echo "  • Use '$DOG_CMD -h' to see available commands"
                elif [ $exit_code -eq 2 ]; then
                    echo "  • Command not found or invalid syntax"
                    echo "  • Use '$DOG_CMD -h' to see available commands"
                else
                    echo "  • Check your Datadog API credentials"
                    echo "  • Verify network connectivity"
                    echo "  • Check command syntax and parameters"
                fi
                
                echo ""
                echo "💡 Common commands:"
                echo "  • monitor show_all"
                echo "  • monitor show <id>"
                echo "  • dashboard list"
                echo "  • metric post"
                echo "  • event post"
                echo "  • host list"
                echo "  • tag list"
                
                exit $exit_code
            fi
            """,
            args=[
                Arg(name="command", description="The command to pass to dog (e.g., 'monitor show_all', 'metric post', 'event post')", required=True)
            ],
            image="python:3.9-slim"
        )

CLITools()