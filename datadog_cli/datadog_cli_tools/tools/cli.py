import sys
from .base import DatadogCLITool, Arg
from kubiya_sdk.tools.registry import tool_registry

class CLITools:
    """Datadog CLI wrapper tools."""

    def __init__(self):
        """Initialize and register all Datadog CLI tools."""
        try:
            tools = [
                self.run_cli_command(),
                self.list_monitors()
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
            sleep 1
            pip install datadog
            sleep 2
            echo "✅ Datadog package installed successfully"
            
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
                echo ""
                echo "💡 For large datasets, use filters to improve performance:"
                echo ""
                echo "Monitor filtering examples:"
                echo "  • monitor show_all --group_states alert,warn"
                echo "    └── Only show monitors currently alerting or warning"
                echo "  • monitor show_all --name 'api'"
                echo "    └── Only show monitors with 'api' in the name"
                echo "  • monitor show_all --tags 'env:production'"
                echo "    └── Only show monitors for production environment"
                echo "  • monitor show_all --monitor_tags 'team:backend'"
                echo "    └── Only show monitors tagged with team:backend"
                echo "  • monitor show_all --group_states alert --tags 'service:api'"
                echo "    └── Combine filters for more specific results"
                echo ""
                echo "Available group_states: all, alert, warn, no_data"
                echo "Tags format: 'key:value' or 'key:value,key2:value2'"
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
            echo "Command: $DOG_CMD --application-key ${DD_APP_KEY} --api-key ${DD_API_KEY} --api_host ${DD_SITE} --timeout 120 $command"
            echo "Timestamp: $(date)"
            echo ""
            
            # Execute the command with timeout and proper output handling
            echo "Executing command..."
            
            # Use a more reliable execution method
            set +e  # Don't exit on error so we can handle it
            
            # Execute with timeout and capture output
            timeout 180 $DOG_CMD --application-key ${DD_APP_KEY} --api-key ${DD_API_KEY} --api_host ${DD_SITE} --timeout 120 $command 2>&1
            exit_code=$?
            
            # Handle the results
            if [ $exit_code -eq 124 ]; then
                echo ""
                echo "❌ Command timed out after 180 seconds"
                echo ""
                echo "💡 This might indicate:"
                echo "  • Authentication issues (check DD_API_KEY, DD_APP_KEY)"
                echo "  • Network connectivity problems"
                echo "  • Invalid command syntax"
                echo "  • Datadog API is slow to respond"
                echo "  • Large dataset - consider using filters or pagination"
                echo ""
                if [[ "$command" == *"monitor show_all"* ]]; then
                    echo "💡 For monitor show_all, try filtering to reduce dataset size:"
                    echo "  • --group_states alert,warn (only alerting monitors)"
                    echo "  • --name 'search_term' (filter by monitor name)"
                    echo "  • --tags 'env:production' (filter by scope tags)"
                    echo "  • --monitor_tags 'team:backend' (filter by monitor tags)"
                    echo ""
                fi
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
                    echo "  • Check command syntax: $DOG_CMD --application-key ${DD_APP_KEY} --api-key ${DD_API_KEY} --api_host ${DD_SITE} --timeout 120 $command"
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
                
                if [[ "$command" == *"monitor show_all"* ]]; then
                    echo ""
                    echo "💡 For monitor show_all, consider using filters:"
                    echo "  • --group_states alert,warn"
                    echo "  • --name 'search_term'"
                    echo "  • --tags 'key:value'"
                    echo "  • --monitor_tags 'key:value'"
                fi
                
                exit $exit_code
            fi
            """,
            args=[
                Arg(name="command", description="The command to pass to dog (e.g., 'monitor show_all', 'metric post', 'event post')", required=True)
            ],
            image="python:3.9-slim"
        )

    def list_monitors(self) -> DatadogCLITool:
        """List Datadog monitors with intelligent filtering options."""
        
        return DatadogCLITool(
            name="datadog_list_monitors",
            description="List Datadog monitors with filtering options to avoid timeouts and get specific results. Use filters to narrow down large datasets efficiently.",
            content="""
            set -e  # Exit on any error

            # Install datadog package if not already installed
            echo "Installing datadog package..."
            pip install datadog > /dev/null 2>&1
            echo "✅ Datadog package installed"

            # Find the dog command
            DOG_CMD=""
            if command -v dog &> /dev/null; then
                DOG_CMD="dog"
            else
                PYTHON_DIR="$(dirname $(which python))"
                if [ -f "$PYTHON_DIR/dog" ] && [ -x "$PYTHON_DIR/dog" ]; then
                    DOG_CMD="$PYTHON_DIR/dog"
                else
                    if python -c "import datadog.dogshell" &> /dev/null; then
                        DOG_CMD="python -m datadog.dogshell"
                    else
                        echo "❌ Error: Could not locate dog command"
                        exit 1
                    fi
                fi
            fi

            # Build the command with filters
            CMD="$DOG_CMD --application-key ${DD_APP_KEY} --api-key ${DD_API_KEY} --api_host ${DD_SITE} --timeout 120 monitor show_all"
            
            # Add filters if provided
            if [ -n "$group_states" ]; then
                CMD="$CMD --group_states $group_states"
            fi
            
            if [ -n "$name_filter" ]; then
                CMD="$CMD --name '$name_filter'"
            fi
            
            if [ -n "$tags" ]; then
                CMD="$CMD --tags '$tags'"
            fi
            
            if [ -n "$monitor_tags" ]; then
                CMD="$CMD --monitor_tags '$monitor_tags'"
            fi

            echo "=== Listing Datadog Monitors ==="
            echo "Command: $CMD"
            echo "Timestamp: $(date)"
            echo ""

            # Execute the command
            timeout 180 $CMD 2>&1
            exit_code=$?

            if [ $exit_code -eq 124 ]; then
                echo ""
                echo "❌ Command timed out after 180 seconds"
                echo "💡 Try using more specific filters to reduce the dataset size"
                exit 1
            elif [ $exit_code -eq 0 ]; then
                echo ""
                echo "✅ Monitors listed successfully"
            else
                echo ""
                echo "❌ Command failed with exit code $exit_code"
                echo "💡 Check your credentials and command syntax"
                exit $exit_code
            fi
            """,
            args=[
                Arg(
                    name="group_states", 
                    description="Filter by monitor states. Options: 'all', 'alert', 'warn', 'no_data'. Use comma-separated for multiple (e.g., 'alert,warn' to show only alerting monitors). Leave empty to show all states.",
                    required=False
                ),
                Arg(
                    name="name_filter", 
                    description="Filter monitors by name. Provide a string to search for in monitor names (e.g., 'api' to find all monitors with 'api' in the name). Case-insensitive partial matching.",
                    required=False
                ),
                Arg(
                    name="tags", 
                    description="Filter by scope tags. Format: 'key:value' or 'key1:value1,key2:value2'. Examples: 'env:production', 'service:api,env:staging'. These are tags on the resources being monitored.",
                    required=False
                ),
                Arg(
                    name="monitor_tags", 
                    description="Filter by monitor tags. Format: 'key:value' or 'key1:value1,key2:value2'. Examples: 'team:backend', 'priority:high,team:frontend'. These are tags applied to the monitors themselves.",
                    required=False
                )
            ],
            image="python:3.9-slim"
        )

CLITools()